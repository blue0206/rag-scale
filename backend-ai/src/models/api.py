from fastapi import UploadFile, File
from pydantic import BaseModel
from typing import Any, Optional, TypeVar, Generic

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    status_code: int
    payload: T

class ApiError(Exception):
    def __init__(self, status_code: int, payload: str, details: Optional[Any]):
        self.success = False
        self.status_code = status_code
        self.payload = payload
        self.details = details

class AuthRequestBody(BaseModel):
    username: str
    password: str

class IngestPayload(BaseModel):
    message: str
    batch_id: str

class ChatRequestBody(BaseModel):
    query: str

class ChatForm:
    def __init__(self, audio: UploadFile = File(...)):
        self.audio = audio
