from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    # MongoDB
    MONGO_DB_ROOT_USERNAME: str
    MONGO_DB_ROOT_PASSWORD: str
    # Neo4j
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    # Tavily
    TAVILY_API_KEY: str
    # S3
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    MINIO_PUBLIC_URL: str
    # RAG
    RAG_COLLECTION_NAME: str = "file_embeddings"
    EMBEDDER_MODEL: str = "nomic-embed-text"
    # mem0
    MEM0_COLLECTION_NAME: str = "mem0_store"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_config() -> Settings:
    return Settings() # type: ignore

env_config = get_config()
