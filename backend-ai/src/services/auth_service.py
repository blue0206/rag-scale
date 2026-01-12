import secrets
from datetime import datetime, timedelta
from pymongo.errors import DuplicateKeyError
from passlib.apps import custom_app_context as pwd_context
from uuid import uuid4, UUID
from models.api import AuthRequestBody
from models.auth import UserInDB
from fastapi import HTTPException
from ..db.mongo import users_collection, sessions_collection


async def register_user(user_data: AuthRequestBody) -> str:
    """
    This function registers a new user by creating the entry in database,
    generating a session token for auth, and returns the user id, username and
    session token.
    """

    # hash password and generate user id
    hash = pwd_context.hash(user_data.password)
    user_id = uuid4()

    # Create user and generate session token for auth.
    try:
        result = await users_collection.insert_one(
            {"id": user_id, "username": user_data.username, "password": hash}
        )

        if not result.acknowledged:
            raise HTTPException(status_code=500, detail="Something went wrong.")
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Username already exists.")
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong.")

    session_token = await generate_session_token(user_id)

    return session_token


async def login_user(user_data: AuthRequestBody) -> str:
    """
    This function logs in a user by first fetching the user details from
    database, then comparing the password with the hashed password.
    If the password is correct, it generates a session token and returns the
    user id, username, and session token, else it raises an error.
    """

    # Get user details from database.
    try:
        user: UserInDB | None = await users_collection.find_one(
            {"username": user_data.username}
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong.")

    # Check if user exists and password is correct.
    if not user or not pwd_context.verify(user_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password.")

    # Generate session token and return response.
    session_token = await generate_session_token(user.id)

    return session_token


async def generate_session_token(user_id: UUID) -> str:
    """
    This function generates a session token and updates the database with the
    session token and corresponding user id with expiry time.
    """

    session_token = secrets.token_hex(32)
    try:
        result = await sessions_collection.insert_one(
            {
                "token": session_token,
                "user_id": user_id,
                "expires_at": datetime.now() + timedelta(days=1),
            }
        )

        if not result.acknowledged:
            raise HTTPException(status_code=500, detail="Something went wrong.")
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong.")

    return session_token


async def get_user_from_token(token: str) -> UUID:
    """
    This function fetches the session details from the database and returns the
    user id if the session is valid, else it raises an error.
    """
    try:
        session = await sessions_collection.find_one({"token": token})
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong.")

    # Check if session is valid and not expired.
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session token.")
    if session.get("expires_at") <= datetime.now():
        raise HTTPException(status_code=401, detail="The session has expired.")

    return session.get("user_id")
