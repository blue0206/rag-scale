from fastapi import APIRouter
from .endpoints.auth import router as auth_router
from .endpoints.ingest import router as ingest_router
from .endpoints.chat import router as chat_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(ingest_router)
api_router.include_router(chat_router)
