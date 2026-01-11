import os

if (
    not os.getenv("GROQ_API_KEY")
    or not os.getenv("NEO4J_URI")
    or not os.getenv("NEO4J_USERNAME")
    or not os.getenv("NEO4J_PASSWORD")
    or not os.getenv("TAVILY_API_KEY")
    or not os.getenv("S3_ACCESS_KEY_ID")
    or not os.getenv("S3_SECRET_ACCESS_KEY")
    or not os.getenv("MONGO_DB_ROOT_USERNAME")
    or not os.getenv("MONGO_DB_ROOT_PASSWORD")
):
    raise ValueError("Missing one or more environment variables.")

env_config = {
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    "NEO4J_URI": os.getenv("NEO4J_URI"),
    "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
    "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
    "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
    "S3_ACCESS_KEY_ID": os.getenv("S3_ACCESS_KEY_ID"),
    "S3_SECRET_ACCESS_KEY": os.getenv("S3_SECRET_ACCESS_KEY"),
    "MONGO_DB_ROOT_USERNAME": os.getenv("MONGO_DB_ROOT_USERNAME"),
    "MONGO_DB_ROOT_PASSWORD": os.getenv("MONGO_DB_ROOT_PASSWORD"),
    "GROQ_MODEL": "openai/gpt-oss-120b",
    "GROQ_BASE_URL": "https://api.groq.com/openai/v1",
    "EMBEDDER_MODEL": "nomic-embed-text",
    "RAG_COLLECTION_NAME": "file_embeddings",
    "MEM0_COLLECTION_NAME": "mem0_store",
}
