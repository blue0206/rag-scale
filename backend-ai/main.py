from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.api.router import api_router
from src.core.db import setup_db_index
from src.models.api import ApiError, ApiResponse
from src.db.s3 import s3_client
from src.services.pubsub_service import pubsub_service
from src.services.queue_service import queue_service
from src.services.batch_tracking_service import batch_tracking_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    print("LIFESPAN: Connecting clients...")
    await setup_db_index()
    pubsub_service.connect()
    await pubsub_service.connect_async()
    queue_service.connect()
    batch_tracking_service.connect()
    await batch_tracking_service.connect_async()
    s3_client.connect()

    yield
    # Shutdown
    print("LIFESPAN: Disonnecting clients...")
    pubsub_service.disconnect()
    await pubsub_service.disconnect_async()
    queue_service.disconnect()
    batch_tracking_service.disconnect()
    await batch_tracking_service.disconnect_async()
    s3_client.disconnect()

app = FastAPI(lifespan=lifespan)

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve static generated audio files.
app.mount("/audio", StaticFiles(directory="generated_audio"), name="audio")

app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_model=ApiResponse[str])
def root_endpoint() -> ApiResponse[str]:
    return ApiResponse(
        success=True, status_code=200, payload="RagScale server is running."
    )


@app.exception_handler(ApiError)
async def api_exception_handler(req: Request, error: ApiError) -> JSONResponse:
    print("API Exception encountered: ", error)

    return JSONResponse(
        status_code=error.status_code,
        content={
            "success": False,
            "payload": error.payload
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(req: Request, error: Exception) -> JSONResponse:
    print(f"An unhandled error occurred: {str(error)}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "payload": "Internal Server Error"
        }
    )

uvicorn.run(app, host="127.0.0.1", port=8000, lifespan="on")
