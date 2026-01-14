from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException
from ..services.auth_service import get_user_from_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Dependency to get the id of the current user from the provided token.
    """

    token = credentials.credentials

    try:
        user_id = await get_user_from_token(token)
        return user_id
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


async def get_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Dependency to get the raw token from the Authorization header.
    This will be used to invalidate the token during logout.
    """

    return credentials.credentials
