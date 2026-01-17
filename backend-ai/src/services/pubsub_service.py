import asyncio
import redis.asyncio as aioredis
from typing import AsyncGenerator
from ..models.ingestion import ProgressState


class PubSubService:
    def __init__(self, host: str = "localhost", port: int = 6379) -> None:
        self.publisher: None | aioredis.Redis = None
        self.subscriber: None | aioredis.Redis = None
        self.connection_details = (host, port)

    async def connect(self) -> None:
        """
        Establish connections for publisher and subscriber.
        """

        if not self.publisher:
            self.publisher = aioredis.Redis(
                host=self.connection_details[0],
                port=self.connection_details[1],
                db=0,
                decode_responses=True,
            )
        if not self.subscriber:
            self.subscriber = aioredis.Redis(
                host=self.connection_details[0],
                port=self.connection_details[1],
                db=0,
                decode_responses=True,
            )

        print("Redis PubSub service connected.")

    async def disconnect(self) -> None:
        """
        Disconnect the redis clients for publisher and subscriber.
        """

        if self.publisher:
            await self.publisher.close()
            self.publisher = None
        if self.subscriber:
            await self.subscriber.close()
            self.subscriber = None

        print("Redis PubSub service disconnected.")

    async def publish(self, channel: str, data: ProgressState) -> None:
        """
        Publishes a JSON message to a specified channel.
        """

        if not self.publisher:
            await self.connect()
        if self.publisher is not None:
            await self.publisher.publish(channel, data.model_dump_json())

    async def subscribe(self, channel: str) -> AsyncGenerator[str, None]:
        """
        Subscribes to a specified channel and yields messages as they arrive.
        """

        if not self.subscriber:
            await self.connect()
        if self.subscriber is not None:
            pubsub = self.subscriber.pubsub()
            await pubsub.subscribe(channel)

            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    yield message["data"]
                    await asyncio.sleep(0.01)


async def publish_ingestion_failure(user_id: str, batch_id: str) -> None:
    """
    Publishes a failure event message to the 'status:{batch_id}' channel
    in case of an errors encountered during ingestion workflow.

    This function accepts the following parameters:
    - user_id: ID of the user.
    - batch_id: ID of the batch.
    """

    await pubsub_service.publish(channel=f"status:{batch_id}", data=ProgressState(
        user_id=user_id,
        status="FAILED",
        progress=0,
        details="Failed to process the PDF(s). Please try again later."
    ))

pubsub_service = PubSubService()
