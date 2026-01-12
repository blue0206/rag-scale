from pydantic import BaseModel
from typing import TypeVar, Generic

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    status_code: int
    payload: T

class AuthRequestBody(BaseModel):
    username: str
    password: str
