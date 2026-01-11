from pydantic import BaseModel
from typing import TypeVar, Generic, Union

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    status_code: int
    payload: Union[T, str]

class RegisterRequestBody(BaseModel):
    username: str
    password: str
