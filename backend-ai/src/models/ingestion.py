from pydantic import BaseModel
from typing import List, Dict

class ChunkingJob(BaseModel):
    user_id: str
    batch_id: str
    object_key: str
    bucket_name: str

class EmbeddingPayload(BaseModel):
    text: str
    metadata: Dict

class EmbeddingJob(BaseModel):
    batch_id: str
    payload: List[EmbeddingPayload]
