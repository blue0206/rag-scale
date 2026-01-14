import os
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..db.s3 import s3_client
from ..services.batch_tracking_service import batch_tracking_service
from ..services.queue_service import queue_service

FILES_DIR = "/tmp/ragscale_downloads"
os.makedirs(FILES_DIR, exist_ok=True)

def load_file(user_id: str, batch_id: str, object_key: str, bucket_name: str) -> List[Document]:
    """
    This function downloads the PDF file from S3 and temporarily saves to disk.
    The saved file is loaded using PyPDFLoader and then deleted from disk.
    The function returns the loaded document with user_id and batch_id stored in metadata.

    This function accepts the following parameters:
    - user_id: ID of the user.
    - batch_id: ID of the batch.
    - object_key: S3 object key where the PDF is stored.
    - bucket_name: Name of the S3 bucket.
    """

    # Load pdf from S3 bucket.
    path = os.path.join(FILES_DIR, object_key.replace("/", "_"))

    print(f"Downloading file from s3://{bucket_name}/{object_key} to {path}.")
    
    s3_client.download_file(
        Bucket=bucket_name,
        Key=object_key,
        Filename=path
    )

    print("File downloaded. Loading document.")

    loader = PyPDFLoader(path)
    docs = loader.load()

    os.remove(path)
    print("Document loaded successfully. Temporary file removed.")
    
    # Store user_id and batch_id in metadata for proper retrieval.
    for doc in docs:
        doc.metadata["user_id"] = user_id
        doc.metadata["batch_id"] = batch_id

    return docs


def split_file(docs: List[Document]) -> List[Document]:
    """
    This function accepts a list of Documents and splits the documents into chunks.
    """

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=400
    )

    print("Splitting document into chunks.")

    chunks = text_splitter.split_documents(docs)
    return chunks


async def offload_chunks(batch_id: str, chunks: List[Document]) -> None:
    """
    This function extracts the text and metadata from the chunks and offloads
    them to the embedding queue for further processing.

    This function also updates the batch tracking service with the number of files chunked
    and the total number of chunks accumulated.

    This function accepts the following parameters:
    - batch_id: ID of the batch.
    - chunks: List of document chunks.
    """
    
    n = len(chunks)

    print(f"Chunking complete. Offloading {n} chunks to embedding queue.")

    # Update status in batch tracking service.
    await batch_tracking_service.increment_field(batch_id=batch_id, field="files_chunked", delta=1)
    await batch_tracking_service.increment_field(batch_id=batch_id, field="total_chunks", delta=n)

    # Offload chunks in batches of 20 to embedding queue.
    for i in range(0, n, 20):
        chunk_subset = chunks[i:i+20]

        payloads = [{"text": chunk.page_content, "metadata": chunk.metadata} for chunk in chunk_subset]
        queue_service.enqueue_embedding_job(batch_id=batch_id, chunks=payloads)

    print("All chunks offloaded to embedding queue.")
