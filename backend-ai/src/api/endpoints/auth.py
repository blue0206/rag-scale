from fastapi import APIRouter, HTTPException
from src.models.api import ApiResponse, AuthRequestBody
from src.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse[str])
async def register(user_data: AuthRequestBody) -> ApiResponse[str]:
    """
    Endpoint to register a new user.
    Takes username and password, creates a new user, and returns a session token.
    """

    try:
        session_token = await register_user(user_data)
        return ApiResponse(success=True, status_code=201, payload=session_token)
    except HTTPException as e:
        return ApiResponse(success=False, status_code=e.status_code, payload=e.detail)
    except Exception:
        return ApiResponse(
            success=False, status_code=500, payload="Internal Server Error"
        )


@router.post("/login", response_model=ApiResponse[str])
async def login(user_data: AuthRequestBody) -> ApiResponse[str]:
    """
    Endpoint to log in an existing user.
    Takes username and password, verifies credentials, and returns a session token.
    """

    try:
        session_token = await login_user(user_data)
        return ApiResponse(success=True, status_code=200, payload=session_token)
    except HTTPException as e:
        return ApiResponse(success=False, status_code=e.status_code, payload=e.detail)
    except Exception:
        return ApiResponse(
            success=False, status_code=500, payload="Internal Server Error"
        )
