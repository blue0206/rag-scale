from datetime import datetime
from pydantic import BaseModel


class UserInDB(BaseModel):
    id: str
    username: str
    password: str


class SessionInDB(BaseModel):
    token: str
    user_id: str
    expires_at: datetime
