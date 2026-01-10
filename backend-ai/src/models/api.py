from pydantic import BaseModel

class ApiResponse(BaseModel):
    success: bool
    status_code: int
    message: str
