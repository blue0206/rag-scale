from dotenv import load_dotenv
load_dotenv()

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.db import setup_db_index
from src.models.api import ApiResponse

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
async def lifespan(app: FastAPI):
    await setup_db_index()
    yield

@app.get("/")
def root_endpoint():
    return ApiResponse(success=True, status_code=200, message="RagScale server is running.")

uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, lifespan=lifespan)
