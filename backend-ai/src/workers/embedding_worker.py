import asyncio
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from ..core.config import env_config
from ..services.pubsub_service import publish_ingestion_failure
from ..services.batch_tracking_service import batch_tracking_service
from models.ingestion import EmbeddingJob


embeddings = OllamaEmbeddings(
    model=env_config["EMBEDDER_MODEL"],
    base_url="http://localhost:11434"
)

def process_chunks(data: EmbeddingJob) -> None:
    """
    This function embeds the given chunks, stores them in Qdrant vector store and updates the batch tracking service.
    """

    try:
        # Convert payloads back to Documents
        documents = [Document(page_content=payload.text, metadata=payload.metadata) for payload in data.payload]
        
        QdrantVectorStore.from_documents(
            documents=documents,
            embedding=embeddings,
            url="http://localhost:6333",
            collection_name=env_config["RAG_COLLECTION_NAME"]
        )

    except Exception as e:
        print(f"Error while processing embedding job: {str(e)}")
        asyncio.run(batch_tracking_service.update_status(batch_id=data.batch_id, status="FAILED"))
        asyncio.run(publish_ingestion_failure(user_id=data.user_id, batch_id=data.batch_id))
        raise e

