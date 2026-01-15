from pydantic import BaseModel
from typing import List, Dict, Literal, Optional


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


class ProgressState(BaseModel):
    user_id: str
    status: Literal["PENDING", "SUCCESS", "FAILED"]
    progress: int
    details: Optional[str]
