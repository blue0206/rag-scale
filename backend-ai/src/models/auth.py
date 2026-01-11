from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class UserInDB(BaseModel):
    id: UUID
    username: str
    password: str


class SessionInDB(BaseModel):
    token: str
    user_id: UUID
    expires_at: datetime


class RegisterServiceResponse(BaseModel):
    user_id: UUID
    username: str
    session_token: str
