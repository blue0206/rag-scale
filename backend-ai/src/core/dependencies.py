from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException
from uuid import UUID
from ..services.auth_service import get_user_from_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    token = credentials.credentials

    try:
        user_id = await get_user_from_token(token)
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e.detail))
