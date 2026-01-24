from websockets import ClientConnection
from asyncio import Task
from operator import add
from openai.types.responses import ResponseInputParam
from pydantic import BaseModel
from typing_extensions import TypedDict, Literal, Optional, Annotated
from dataclasses import dataclass


class State(TypedDict):
    user_id: str
    user_query: str
    messages: Annotated[ResponseInputParam, add]
    query_type: Optional[Literal["NORMAL", "RETRIEVAL"]]


class ChatEvent(BaseModel):
    type: Literal["status", "transcription", "text", "audio", "error"]
    content: str


class StreamPayload(BaseModel):
    data: str
    status: Optional[Literal["Finished", "In Progress"]]


@dataclass
class TTSClient:
    websocket: ClientConnection
    receiver_task: Task
    stream_id: str
