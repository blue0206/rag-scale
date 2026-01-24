import base64
from typing import AsyncGenerator
from redis.asyncio import Redis
from ..models.chat import StreamPayload


class StreamService:
    def __init__(self, host: str = "localhost", port: int = 6379):
        self.client: Redis | None = None
        self.connection_details = (host, port)

    async def connect(self) -> None:
        """
        Connects the redis streaming client.
        """

        if not self.client:
            self.client = Redis(
                host=self.connection_details[0], port=self.connection_details[1], db=2
            )
            print("Redis Streaming Client connected.")

    async def disconnect(self) -> None:
        """
        Disconnects the redis streaming client.
        """

        if self.client:
            await self.client.close()
            self.client = None
            print("Redis Streaming Client disconnected.")

    async def write_stream(self, stream_id: str, data: bytes) -> None:
        """
        Writes the data to redis stream for a specific stream_id.
        """

        if not self.client:
            await self.connect()
        if self.client:
            b64data = base64.b64encode(data).decode("utf-8")
            await self.client.xadd(
                name=stream_id,
                fields={
                    "data": StreamPayload(
                        data=b64data, status="In Progress"
                    ).model_dump_json()
                },
            )
            await self.client.expire(name=stream_id, time=500)

    async def end_stream(self, stream_id: str) -> None:
        """
        Send the end signal to the stream.
        """

        if not self.client:
            await self.connect()
        if self.client:
            await self.client.xadd(
                name=stream_id,
                fields={
                    "data": StreamPayload(data="", status="Finished").model_dump_json()
                },
            )
            await self.client.expire(name=stream_id, time=500)

    async def read_stream(self, stream_id: str) -> AsyncGenerator[bytes, None]:
        """
        Reads the data from redis stream for a specific stream_id.
        """

        if not self.client:
            await self.connect()
        if self.client:
            last_id = "0-0"

            while True:
                result = await self.client.xread(
                    streams={stream_id: last_id}, count=1, block=60000
                )

                if not result:
                    break

                stream_key, data = result[0]

                for message_id, message in data:
                    last_id = message_id

                    if b"data" in message:
                        json_data = message[b"data"]
                        parsed_data = StreamPayload.model_validate_json(json_data)

                        if parsed_data.status == "Finished":
                            await self.client.delete(stream_key)
                            return
                        else:
                            audio_bytes = base64.b64decode(parsed_data.data)
                            yield audio_bytes

            await self.client.delete(stream_id)


stream_service = StreamService()
