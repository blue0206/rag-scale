import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, BackgroundTasks, Depends, Request, UploadFile
from fastapi.responses import StreamingResponse
from ...models.api import ChatForm, ChatRequestBody
from ...models.chat import ChatEvent
from ...core.dependencies import get_current_user
from ...services.tts_service import tts_service
from ...services.voice_agent import speech_to_text
from ...services.llm_service import stream_llm_response
from ...services.streaming_service import stream_service
from ...db.mem0 import mem0_client

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/text")
async def chat_handler(
    background_tasks: BackgroundTasks,
    req: Request,
    user_id: str = Depends(get_current_user),
) -> StreamingResponse:
    """
    This handler tackles text-based chat requests. It authenticates the user and streams
    back a series of Server-Sent Events (SSE) containing the LLM's response.
    """

    body = await req.json()
    validated_body = ChatRequestBody.model_validate(body)

    return StreamingResponse(
        text_workflow(
            user_query=validated_body.query,
            user_id=user_id,
            background_tasks=background_tasks,
        ),
        media_type="text/event-stream",
    )


@router.post("/voice")
async def voice_handler(
    background_tasks: BackgroundTasks,
    form: ChatForm = Depends(),
    user_id: str = Depends(get_current_user),
) -> StreamingResponse:
    """
    This handler tackles voice-based chat requests. Accepts multipart/form-data with an 'audio' file.
    It authenticates the user, transcribes the audio, generates a text response (streamed via SSE),
    generates a final audio response, and sends a final SSE event with the audio URL.
    """

    return StreamingResponse(
        audio_workflow(
            data=form.audio, user_id=user_id, background_tasks=background_tasks
        ),
        media_type="text/event-stream",
    )


@router.get("/audio-stream/{stream_id}")
async def audio_stream_handler(stream_id: str):
    """
    This handler streams the audio for a specific stream_id.
    """

    return StreamingResponse(
        stream_service.read_stream(stream_id=stream_id), media_type="audio/mp3"
    )


async def text_workflow(
    user_query: str, user_id: str, background_tasks: BackgroundTasks
) -> AsyncGenerator[str, None]:
    """
    This functions initiates the text query workflow by
    simply streaming the LLM text response to client.
    """

    try:
        yield f"data: {ChatEvent(type='status', content='Thinking....').model_dump_json()}\n\n"
        full_response = ""

        # Stream LLM response to client.
        async for delta in stream_llm_response(
            user_id=user_id, user_query=user_query, is_voice=False
        ):
            if delta:
                full_response += delta
                yield f"data: {ChatEvent(type='text', content=delta).model_dump_json()}\n\n"

        # mem0 handles updating factual, episodic, and semantic memory.
        # This process is CPU-intensive as the embedding model is on my local machine
        # and hence blocks the server. In production, this won't be needed
        # as the embedding would essentially be a simple API call.
        background_tasks.add_task(
            mem0_client.add_memories,
            user_id,
            [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": full_response},
            ],
        )
    except Exception as e:
        print(f"Error occurred while streaming for user {user_id}: {str(e)}")

        yield f"data: {ChatEvent(type='error', content=f'An error occurred: {str(e)}').model_dump_json()}\n\n"
    finally:
        print(f"Streaming for user {user_id} has ended.")


async def audio_workflow(
    data: UploadFile, user_id: str, background_tasks: BackgroundTasks
) -> AsyncGenerator[str, None]:
    """
    This function initiates the audio query workflow.

    1. The audio file is first transcribed by the STT handler.
    2. We open a TTS (ElevenLabs) client connection and within it start streaming.
    3. The text response chunks are streamed to the open websocket connection to TTS API.
    4. The text response chunks are streamed to client via this function.
    5. The audio bytes are served on a separate endpoint based on stream_id, which is yielded so that client can connect.
    """

    try:
        # 1. TRANSCRIBE THE AUDIO QUERY-----------------------------------------------------------------
        yield f"data: {ChatEvent(type='status', content='Transcribing audio...').model_dump_json()}\n\n"

        # Generate transcription and send it as event too in order to update UI.
        transcribed_text = await speech_to_text(file=data)
        yield f"data: {ChatEvent(type='transcription', content=transcribed_text).model_dump_json()}\n\n"

        user_query = transcribed_text

        # 2. GENERATE LLM TEXT RESPONSE, STREAM TO TTS API AND TO CLIENT--------------------------------
        yield f"data: {ChatEvent(type='status', content='Thinking....').model_dump_json()}\n\n"
        full_response = ""

        async with tts_service.connect() as tts_client:
            # Yield stream_id so that client can connect to the endpoint.
            yield f"data: {ChatEvent(type='audio', content=tts_client.stream_id).model_dump_json()}\n\n"

            # Stream LLM response to client.
            async for delta in stream_llm_response(
                user_id=user_id, user_query=user_query, is_voice=True
            ):
                if delta:
                    full_response += delta
                    await tts_service.sender(
                        websocket=tts_client.websocket, payload=delta
                    )
                    yield f"data: {ChatEvent(type='text', content=delta).model_dump_json()}\n\n"

            await tts_service.sender(websocket=tts_client.websocket, payload="")

            # Set up a timer of 30 seconds in case the receiver_task never finishes.
            try:
                if not tts_client.receiver_task.done():
                    await asyncio.wait_for(tts_client.receiver_task, 30.0)
            except asyncio.CancelledError:
                print("TTS Client Connection closed.")


        # mem0 handles updating factual, episodic, and semantic memory.
        # This process is CPU-intensive and hence blocks the server. Therefore, we use an
        background_tasks.add_task(
            mem0_client.add_memories,
            user_id,
            [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": full_response},
            ],
        )
    except Exception as e:
        print(f"Error occurred while streaming for user {user_id}: {str(e)}")

        yield f"data: {ChatEvent(type='error', content=f'An error occurred: {str(e)}').model_dump_json()}\n\n"
    finally:
        print(f"Streaming for user {user_id} has ended.")
