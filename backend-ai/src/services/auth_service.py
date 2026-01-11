import secrets
from passlib.apps import custom_app_context as pwd_context
from uuid import uuid4, UUID
from ..db.mongo import users_collection, sessions_collection
from models.api import AuthRequestBody
from models.auth import UserInDB, SessionInDB, AuthServiceResponse


async def register_user(user_data: AuthRequestBody) -> AuthServiceResponse:
    """
    This function registers a new user by creating the entry in database,
    generating a session token for auth, and returns the user id, username and
    session token.
    """

    # hash password
    hash = pwd_context.hash(user_data.password)

    # Create user and generate session token for auth.
    try:
        new_user: UserInDB = await users_collection.insert_one(
            {"id": uuid4(), "username": user_data.username, "password": hash}
        )

        session_token = await generate_session_token(new_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RegisterServiceResponse(
        user_id=new_user.id, username=new_user.username, session_token=session_token
    )


async def generate_session_token(user_id: UUID) -> str:
    try:
        session_token = secrets.token_hex(32)
        session: SessionInDB = await sessions_collection.insert_one(
            {
                "token": session_token,
                "user_id": user_id,
                "expires_at": datetime.now() + timedelta(days=1),
            }
        )

        return session.token
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
