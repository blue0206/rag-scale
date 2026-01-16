from mem0 import Memory
from ..core.config import env_config

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": env_config.MEM0_COLLECTION_NAME,
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 768
        }
    },
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": env_config.NEO4J_URI,
            "username": env_config.NEO4J_USERNAME,
            "password": env_config.NEO4J_PASSWORD
        }
    },
    "llm": {
        "provider": "groq",
        "config": {
            "model": env_config.GROQ_MODEL,
            "api_key": env_config.GROQ_API_KEY
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": env_config.EMBEDDER_MODEL,
            "ollama_base_url": "http://localhost:11434"
        }
    }
}

mem0_client = Memory.from_config(config)
