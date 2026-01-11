import secrets
from passlib.apps import custom_app_context as pwd_context
from uuid import uuid4
from ..db.mongo import users_collection, sessions_collection
from models.api import RegisterRequestBody
from models.auth import UserInDB, SessionInDB, RegisterServiceResponse


async def register_user(user_data: RegisterRequestBody) -> RegisterServiceResponse:
    """
    This function registers a new user by creating the entry in database,
    generating a session token for auth, and returns the user id, username and
    session token.
    """

    # hash password
    hash = pwd_context.hash(user_data.password)

    # Create user
    try:
        new_user: UserInDB = await users_collection.insert_one(
            {"id": uuid4(), "username": user_data.username, "password": hash}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate session token for auth.
    try:
        session_token = secrets.token_hex(32)
        session: SessionInDB = await sessions_collection.insert_one(
            {
                "token": session_token,
                "user_id": new_user.id,
                "expires_at": datetime.now() + timedelta(days=1),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RegisterServiceResponse(
        user_id=new_user.id, username=new_user.username, session_token=session.token
    )
