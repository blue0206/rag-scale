import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..db.redis import embedding_queue
from .embedding_worker import process_chunks
from ..db.s3 import s3_client

FILES_DIR = "/tmp/ragscale_downloads"
os.makedirs(FILES_DIR, exist_ok=True)

def load_file(user_id: str, batch_id: str, object_key: str, bucket_name: str) -> List:
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


def split_file(docs: list) -> list:
    """
    Splits the document into chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=400
    )

    chunks = text_splitter.split_documents(docs)
    return chunks

def offload_chunks(chunks: list) -> list:
    """
    Sends the chunks to the chunking queue.
    """
    
    n = len(chunks)
    jobs = []

    for i in range(0, n, 20):
        chunk_subset = chunks[i:i+20]
        job = embedding_queue.enqueue(process_chunks, chunk_subset)
        jobs.append(job)

    return jobs
