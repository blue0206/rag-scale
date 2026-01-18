from contextlib import asynccontextmanager
from typing import AsyncGenerator
from mem0 import AsyncMemory
from mem0.configs.base import (
    MemoryConfig,
    VectorStoreConfig,
    GraphStoreConfig,
    LlmConfig,
    EmbedderConfig,
)
from mem0.graphs.configs import Neo4jConfig
from openai.types.responses import ResponseInputParam
from ..core.config import env_config

class Mem0Service:
    def __init__(self) -> None:
        self.config = MemoryConfig(
            vector_store=VectorStoreConfig(
                provider="qdrant",
                config={
                    "collection_name": env_config.MEM0_COLLECTION_NAME,
                    "host": "localhost",
                    "port": 6333,
                    "embedding_model_dims": 768,
                },
            ),
            graph_store=GraphStoreConfig(
                provider="neo4j",
                config=Neo4jConfig(
                    url=env_config.NEO4J_URI,
                    username=env_config.NEO4J_USERNAME,
                    password=env_config.NEO4J_PASSWORD,
                    database=None,
                    base_label=None,
                ),
            ),
            llm=LlmConfig(
                provider="groq",
                config={"model": env_config.GROQ_MODEL, "api_key": env_config.GROQ_API_KEY},
            ),
            embedder=EmbedderConfig(
                provider="ollama",
                config={
                    "model": env_config.EMBEDDER_MODEL,
                    "ollama_base_url": "http://localhost:11434",
                },
            ),
        )

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[AsyncMemory, None]:
        """
        An async context manager that provides a Mem0 client instance.
        """

        mem0_client = AsyncMemory(config=self.config)
        try:
            yield mem0_client
        finally:
            print("Mem0 client context closed.")

    async def search_memories(self, user_query: str, user_id: str):
        """
        Searches for memories of a specific user based on their query.
        """

        async with self.get_client() as memory:
            return await memory.search(query=user_query, user_id=user_id)
    
    async def add_memories(self, user_id: str, messages: ResponseInputParam) -> None:
        """
        Adds memories about the user based on the current conversation.
        """

        async with self.get_client() as memory:
            await memory.add(
                user_id=user_id,
                messages=messages
            )

mem0_client = Mem0Service()
