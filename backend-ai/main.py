import uvicorn
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.router import api_router
from src.core.db import setup_db_index
from src.models.api import ApiResponse
from src.services.pubsub_service import pubsub_service
from services.queue_service import queue_service

load_dotenv()
app = FastAPI()

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    await setup_db_index()
    await pubsub_service.connect()
    queue_service.connect()

    yield
    # Shutdown
    await pubsub_service.disconnect()
    queue_service.disconnect()


app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_model=ApiResponse[str])
def root_endpoint() -> ApiResponse[str]:
    return ApiResponse(
        success=True, status_code=200, payload="RagScale server is running."
    )


uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, lifespan="on")
