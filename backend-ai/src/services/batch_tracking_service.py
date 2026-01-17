import redis
import redis.asyncio as aioredis
from typing import Literal
from uuid import uuid4
from ..models.ingestion import BatchDetails


class BatchTrackingService:
    def __init__(self, host: str = "localhost", port: int = 6379) -> None:
        self.redis_client: redis.Redis | None = None
        self.aioredis_client: aioredis.Redis | None = None
        self.connection_details = (host, port)

    def connect(self) -> None:
        """
        Establish the redis connection.
        """

        if not self.redis_client:
            self.redis_client = redis.Redis(
                host=self.connection_details[0],
                port=self.connection_details[1],
                db=0,
                decode_responses=True,
            )

        print("Redis Batch Tracking Service connected.")

    async def connect_async(self) -> None:
        """
        Establish the redis connection for the async client.
        """

        if not self.aioredis_client:
            self.aioredis_client = aioredis.Redis(
                host=self.connection_details[0],
                port=self.connection_details[1],
                db=0,
                decode_responses=True,
            )

        print("Redis Batch Tracking Service (Async) connected.")


    def disconnect(self) -> None:
        """
        Disconnect the redis client.
        """

        if self.redis_client:
            self.redis_client.close()
            self.redis_client = None

        print("Redis Batch Tracking Service disconnected.")

    async def disconnect_async(self) -> None:
        """
        Disconnect the async redis client.
        """

        if self.aioredis_client:
            await self.aioredis_client.close()
            self.aioredis_client = None

        print("Redis Batch Tracking Service (Async) disconnected.")

    async def create_batch(self, total_files: int, user_id: str) -> str:
        """
        Initializes a new batch in Redis to track the processing status of uploaded files.
        """

        batch_id = str(uuid4())

        if not self.aioredis_client:
            await self.connect_async()
        if self.aioredis_client is not None:
            await self.aioredis_client.hset(
                f"batch:{batch_id}",
                mapping={
                    "user_id": user_id,
                    "total_files": total_files,
                    "files_chunked": 0,
                    "total_chunks": 0,
                    "chunks_embedded": 0,
                    "status": "PENDING",
                },
            )  # type: ignore

        return batch_id

    def increment_field(
        self,
        batch_id: str,
        field: Literal["files_chunked", "total_chunks", "chunks_embedded"],
        delta: int,
    ) -> None:
        """
        Increments a specific field in the batch hash by a given delta.
        """

        if not self.redis_client:
            self.connect()
        if self.redis_client is not None:
            self.redis_client.hincrby(f"batch:{batch_id}", field, delta)

    def update_status(
        self, batch_id: str, status: Literal["PENDING", "SUCCESS", "FAILED"]
    ) -> None:
        """
        Updates the status of the batch.
        """

        if not self.redis_client:
            self.connect()
        if self.redis_client is not None:
            self.redis_client.hset(f"batch:{batch_id}", "status", status)
    
    def get_batch_status(self, batch_id: str) -> BatchDetails | None:
        """
        Retrieves the current status of the batch.
        """

        if not self.redis_client:
            self.connect()
        if self.redis_client is not None:
            data = self.redis_client.hgetall(f"batch:{batch_id}")
            if not data:
                return None

            batch_data = BatchDetails.model_validate(data)

            return BatchDetails(
                user_id=batch_data.user_id,
                total_files=int(batch_data.total_files),
                files_chunked=int(batch_data.files_chunked),
                total_chunks=int(batch_data.total_chunks),
                chunks_embedded=int(batch_data.chunks_embedded),
                status=batch_data.status,
            )

    async def get_batch_status_async(self, batch_id: str) -> BatchDetails | None:
        """
        Asynchronously retrieves the current status of the batch.
        """

        if not self.aioredis_client:
            await self.connect_async()
        if self.aioredis_client is not None:
            batch_data = await self.aioredis_client.hgetall(f"batch:{batch_id}")  # type: ignore
            if not batch_data:
                return None

            return BatchDetails(
                user_id=batch_data.get("user_id", ""),
                total_files=int(batch_data.get("total_files", 0)),
                files_chunked=int(batch_data.get("files_chunked", 0)),
                total_chunks=int(batch_data.get("total_chunks", 0)),
                chunks_embedded=int(batch_data.get("chunks_embedded", 0)),
                status=batch_data.get("status", "NONE"),
            )


def check_ingestion_failure(batch_id: str) -> bool:
    """
    This function checks the current status of batch in redis hash and returns
    True if it is failed or missing, else False.
    """

    batch_details = batch_tracking_service.get_batch_status(batch_id=batch_id)

    if batch_details is None:
        return True
    else:
        return batch_details.status == "FAILED" or batch_details.status == "NONE"


batch_tracking_service = BatchTrackingService()
