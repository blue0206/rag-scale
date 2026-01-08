from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..db.redis import embedding_queue
from ..workers.ingestion_worker import process_chunks

def load_file(user_id: str, pdf_id: str) -> list:
    """
    Loads the pdf file from files directory and returns the document.
    """

    path = Path(__file__).parent.parent.parent / "files" / f"{user_id}_{pdf_id}.pdf"
    loader = PyPDFLoader(path)

    docs = loader.load()
    
    # Store user_id and pdf_id in metadata for proper retrieval.
    for doc in docs:
        doc.metadata["user_id"] = user_id
        doc.metadata["pdf_id"] = pdf_id

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
