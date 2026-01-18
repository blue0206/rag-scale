from typing import AsyncGenerator, Union
from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import StreamingResponse
from ...models.api import ChatForm, ChatRequestBody
from ...models.chat import ChatEvent
from ...core.dependencies import get_current_user
from ...services.voice_agent import speech_to_text, text_to_speech
from ...services.llm_service import stream_llm_response

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/chat/text")
async def chat_handler(
    req: Request, user_id: str = Depends(get_current_user)
) -> StreamingResponse:
    """
    This handler tackles text-based chat requests. It authenticates the user and streams
    back a series of Server-Sent Events (SSE) containing the LLM's response.
    """

    body = await req.json()
    validated_body = ChatRequestBody.model_validate(body)

    return StreamingResponse(
        stream_chat(data=validated_body.query, user_id=user_id),
        media_type="text/event-stream",
    )


@router.post("/chat/voice")
async def voice_handler(
    form: ChatForm = Depends(), user_id: str = Depends(get_current_user)
) -> StreamingResponse:
    """
    This handler tackles voice-based chat requests. Accepts multipart/form-data with an 'audio' file.
    It authenticates the user, transcribes the audio, generates a text response (streamed via SSE),
    generates a final audio response, and sends a final SSE event with the audio URL.
    """

    return StreamingResponse(
        stream_chat(data=form.audio, user_id=user_id), media_type="text/event-stream"
    )


async def stream_chat(
    data: Union[UploadFile, str], user_id: str
) -> AsyncGenerator[str, None]:
    """
    This function handles core streaming based on the type of query provided.

    If the query provided is in text format, then we simply stream LLM response
    without involving voice-agents in the loop.

    If the query provided is an audio file, then:
    1. It is first transcribed using STT api.
    2. The transcribed text is passed to LangGraph workflow to stream LLM text response.
    3. The entire text response is accumulate and passed to TTS api for audio output.
    4. The audio file is served as static asset and the filename is sent as one final event.

    """
    try:
        is_voice = not isinstance(data, str)
        user_query: str

        # 1.---------------- Get the transcribed text from user audio. ---------------
        if is_voice:
            yield f"data: {ChatEvent(type='status', content='Transcribing audio...').model_dump_json()}\n\n"

            # Generate transcription and send it as event too in order to update UI.
            transcribed_text = await speech_to_text(file=data)
            yield f"data: {ChatEvent(type='transcription', content=transcribed_text).model_dump_json()}\n\n"

            user_query = transcribed_text
        else:
            user_query = data

        # 2.--------- Invoke langgraph workflow to answer the transcribed user query.----------
        # Note that in case user_query was not audio, this is the only executed part of this function.
        yield f"data: {ChatEvent(type='status', content='Thinking....').model_dump_json()}\n\n"

        full_response = ""  # Will be fed to the TTS handler if user query was in voice.
        # Stream LLM response to client.
        async for delta in stream_llm_response(user_id=user_id, user_query=user_query):
            if delta:
                full_response += delta
                yield f"data: {ChatEvent(type='text', content=delta).model_dump_json()}\n\n"

        # 3.---------- If the user query was audio, we provide audio response. -------------
        # We provide accumulated response to TTS handler.
        if is_voice:
            yield f"data: {ChatEvent(type='status', content='Generating audio....').model_dump_json()}\n\n"

            output_filename = await text_to_speech(
                transcript=full_response, user_id=user_id
            )

            audio_url = f"/audio/{output_filename}"
            yield f"data: {ChatEvent(type='audio', content=audio_url).model_dump_json()}\n\n"
    except Exception as e:
        print(f"Error occurred while streaming for user {user_id}: {str(e)}")

        yield f"data: {ChatEvent(type='error', content=f'An error occurred: {str(e)}').model_dump_json()}\n\n"
    finally:
        print(f"Streaming for user {user_id} has ended.")
