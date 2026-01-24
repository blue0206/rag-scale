import asyncio
import base64
import websockets
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import uuid4
from ..core.config import env_config
from ..models.chat import TTSClient
from ..services.streaming_service import stream_service


class ElevenLabsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.uri = "wss://api.elevenlabs.io/v1/text-to-speech/hpp4J3VqNfWAUOO0d1Us/stream-input"

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[TTSClient, None]:
        """
        Establishes a websocket connection with ElevenLabs, starts the receiver task in background,
        and yields the class instance.
        """
        websocket = None
        receiver_task = None

        try:
            websocket = await websockets.connect(
                uri=self.uri, additional_headers={"xi-api-key": self.api_key}
            )

            await websocket.send(
                json.dumps({"text": " ", "model_id": "eleven_multilingual_v2"})
            )

            stream_id = str(uuid4())
            receiver_task = asyncio.create_task(
                self.receiver(websocket=websocket, stream_id=stream_id)
            )

            client = TTSClient(
                websocket=websocket, receiver_task=receiver_task, stream_id=stream_id
            )

            print("TTS Client is connected.")
            yield client
        except Exception as e:
            print("Error occurred in TTS context manager: ", e)
            raise e
        finally:
            if websocket:
                await websocket.close()
                websocket = None

            if receiver_task and not receiver_task.done():
                receiver_task.cancel()
            print("TTS Client context closed.")

    async def receiver(
        self, websocket: websockets.ClientConnection, stream_id: str
    ) -> None:
        """
        Listens for incoming messages and writes them to the redis stream.
        """

        try:
            while True:
                data = await websocket.recv()
                parsed_data = json.loads(data)

                if parsed_data.get("audio"):
                    audio_bytes = base64.b64decode(parsed_data["audio"])
                    await stream_service.write_stream(
                        stream_id=stream_id, data=audio_bytes
                    )
                elif parsed_data.get("isFinal") and parsed_data.get("isFinal"):
                    break
        except websockets.exceptions.ConnectionClosedOK:
            print("ElevenLabs connection closed gracefully.")
        except websockets.exceptions.ConnectionClosedError as e:
            print("ElevenLabs connection closed with error: ", e)
        finally:
            await stream_service.end_stream(stream_id=stream_id)

    async def sender(
        self, websocket: websockets.ClientConnection, payload: str
    ) -> None:
        """
        Sends the text chunks via websocket connection.
        """

        await websocket.send(json.dumps({"text": payload}))


tts_service = ElevenLabsService(env_config.ELEVENLABS_API_KEY)
