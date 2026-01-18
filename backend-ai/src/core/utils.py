import asyncio
from langchain_ollama import OllamaEmbeddings
from typing import List
from .config import env_config

embeddings = OllamaEmbeddings(
    model=env_config.EMBEDDER_MODEL,
    base_url="http://localhost:11434",
)


async def get_query_embeddings(user_query: str) -> List[float]:
    """
    Runs the synchronous, CPU-bound embedding function in a separate thread
    to avoid blocking the main FastAPI event loop.
    """
    return await asyncio.to_thread(embeddings.embed_query, user_query)
