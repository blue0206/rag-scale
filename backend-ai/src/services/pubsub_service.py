import asyncio
import redis
import redis.asyncio as aioredis
from typing import AsyncGenerator
from ..models.ingestion import ProgressState


class PubSubService:
    def __init__(self, host: str = "localhost", port: int = 6379) -> None:
        self.publisher: None | redis.Redis = None
        self.async_publisher: None | aioredis.Redis = None
        self.async_subscriber: None | aioredis.Redis = None
        self.connection_details = (host, port)

    def connect(self) -> None:
        """
        Establish connection for synchronous publisher.
        """

        if not self.publisher:
            self.publisher = redis.Redis(
                host=self.connection_details[0],
                port=self.connection_details[1],
                db=1,
                decode_responses=True,
            )

        print("Redis synchronous publisher connected.")

    async def connect_async(self) -> None:
        """
        Establish connections for async publisher and subscriber.
        """

        if not self.async_publisher:
            self.async_publisher = aioredis.Redis(
                host=self.connection_details[0],
                port=self.connection_details[1],
                db=1,
                decode_responses=True,
            )
        if not self.async_subscriber:
            self.async_subscriber = aioredis.Redis(
                host=self.connection_details[0],
                port=self.connection_details[1],
                db=1,
                decode_responses=True,
            )

        print("Redis PubSub service connected.")

    def disconnect(self) -> None:
        """
        Disconnect the synchronous redis publisher client.
        """

        if self.publisher:
            self.publisher.close()
            self.publisher = None

        print("Redis synchronous publisher disconnected.")

    async def disconnect_async(self) -> None:
        """
        Disconnect the redis clients for publisher and subscriber.
        """

        if self.async_publisher:
            await self.async_publisher.close()
            self.async_publisher = None
        if self.async_subscriber:
            await self.async_subscriber.close()
            self.async_subscriber = None

        print("Redis PubSub service disconnected.")

    def publish(self, channel: str, data: ProgressState) -> None:
        """
        This method is synchronous.
        Publishes a JSON message to a specified channel.
        """

        if not self.publisher:
            self.connect()
        if self.publisher is not None:
            self.publisher.publish(channel, data.model_dump_json())

    async def publish_async(self, channel: str, data: ProgressState) -> None:
        """
        Publishes a JSON message to a specified channel.
        """

        if not self.async_publisher:
            await self.connect_async()
        if self.async_publisher is not None:
            await self.async_publisher.publish(channel, data.model_dump_json())

    async def subscribe(self, channel: str) -> AsyncGenerator[str, None]:
        """
        Subscribes to a specified channel and yields messages as they arrive.
        """

        if not self.async_subscriber:
            await self.connect_async()
        if self.async_subscriber is not None:
            pubsub = self.async_subscriber.pubsub()
            await pubsub.subscribe(channel)

            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    yield message["data"]
                    await asyncio.sleep(0.01)


def publish_ingestion_failure(user_id: str, batch_id: str) -> None:
    """
    Publishes a failure event message to the 'status:{batch_id}' channel
    in case of an errors encountered during ingestion workflow.
    This method is synchronous.

    This function accepts the following parameters:
    - user_id: ID of the user.
    - batch_id: ID of the batch.
    """

    pubsub_service.publish(channel=f"status:{batch_id}", data=ProgressState(
        user_id=user_id,
        status="FAILED",
        progress=0,
        details="Failed to process the PDF(s). Please try again later."
    ))

pubsub_service = PubSubService()
