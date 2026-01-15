import asyncio
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from ..core.config import env_config
from ..services.pubsub_service import pubsub_service, publish_ingestion_failure
from ..services.batch_tracking_service import batch_tracking_service
from models.ingestion import EmbeddingJob, ProgressState


embeddings = OllamaEmbeddings(
    model=env_config["EMBEDDER_MODEL"], base_url="http://localhost:11434"
)


def process_chunks(data: EmbeddingJob) -> None:
    """
    This function embeds the given chunks, stores them in Qdrant vector store and updates the batch tracking service.
    """

    try:
        # Convert payloads back to Documents
        documents = [
            Document(page_content=payload.text, metadata=payload.metadata)
            for payload in data.payload
        ]

        QdrantVectorStore.from_documents(
            documents=documents,
            embedding=embeddings,
            url="http://localhost:6333",
            collection_name=env_config["RAG_COLLECTION_NAME"],
        )

        asyncio.run(
            update_embedding_status(data.user_id, data.batch_id, len(data.payload))
        )
    except ValueError as ve:
        asyncio.run(
            publish_ingestion_failure(user_id=data.user_id, batch_id=data.batch_id)
        )
        raise ve
    except Exception as e:
        print(f"Error while processing embedding job: {str(e)}")
        asyncio.run(
            batch_tracking_service.update_status(
                batch_id=data.batch_id, status="FAILED"
            )
        )
        asyncio.run(
            publish_ingestion_failure(user_id=data.user_id, batch_id=data.batch_id)
        )
        raise e


async def update_embedding_status(user_id: str, batch_id: str, n: int) -> None:
    """
    This function updates the batch tracking service with the number of chunks embedded.

    This function accepts the following parameters:
    - user_id: ID of the user.
    - batch_id: ID of the batch.
    - n: Number of chunks embedded.
    """

    print(f"Embedding of {n} chunks complete. Updating batch status.")
    await batch_tracking_service.increment_field(
        batch_id=batch_id, field="chunks_embedded", delta=n
    )
    print("Batch status updated.")

    # Check the current status of the batch.
    batch_status = await batch_tracking_service.get_batch_status(batch_id=batch_id)

    # If batch status is None, raise error and publish failure event.
    if batch_status is None:
        print(f"Batch ID {batch_id} not found in tracking service.")

        await publish_ingestion_failure(user_id=user_id, batch_id=batch_id)
        raise ValueError(f"Batch ID {batch_id} not found in redis hash.")

    # If all chunks are embedded, update the batch status to SUCCESS.
    if (
        batch_status.chunks_embedded == batch_status.total_chunks
        and batch_status.files_chunked == batch_status.total_files
    ):
        await batch_tracking_service.update_status(batch_id=batch_id, status="SUCCESS")
        print(f"All chunks embedded for batch {batch_id}. Batch marked as SUCCESS.")

        await pubsub_service.publish(
            channel=f"status:{batch_id}",
            data=ProgressState(
                user_id=batch_status.user_id,
                status="SUCCESS",
                progress=100,
                # The details message should be neatly formatted string with summary.
                details=f"The file(s) have been processed successfully.\nSummary:\n- Total Files: {batch_status.total_files}\n- Total Chunks: {batch_status.total_chunks}",
            ),
        )

    # If not all chunks are embedded, publish progress update.
    else:
        progress = (
            int((batch_status.chunks_embedded / batch_status.total_chunks) * 100)
            if batch_status.total_chunks > 0
            else 0
        )
        print(f"Batch {batch_id} embedding progress: {progress}%.")

        await pubsub_service.publish(
            channel=f"status:{batch_id}",
            data=ProgressState(
                user_id=batch_status.user_id,
                status="PENDING",
                progress=progress,
                details=f"{batch_status.files_chunked} out of {batch_status.total_files} files chunked and {batch_status.chunks_embedded} out of {batch_status.total_chunks} chunks embedded.",
            ),
        )
