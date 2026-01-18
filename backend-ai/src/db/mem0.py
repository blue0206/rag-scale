from mem0 import Memory
from mem0.configs.base import (
    MemoryConfig,
    VectorStoreConfig,
    GraphStoreConfig,
    LlmConfig,
    EmbedderConfig,
)
from mem0.graphs.configs import Neo4jConfig
from ..core.config import env_config

config = MemoryConfig(
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

mem0_client = Memory(config=config)
