from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from ..core.config import env_config

def process_chunks(chunks: list) -> None:
    embeddings = OllamaEmbeddings(
        model=env_config["EMBEDDER_MODEL"],
        base_url="http://localhost:11434"
    )

    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url="http://localhost:6333",
        collection_name=env_config["RAG_COLLECTION_NAME"]
    )
