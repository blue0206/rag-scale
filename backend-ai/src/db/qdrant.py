from qdrant_client import QdrantClient

vector_client = QdrantClient(
    host="localhost",
    port=6333,
)
