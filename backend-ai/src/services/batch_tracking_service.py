import redis.asyncio as aioredis
from typing import Literal
from uuid import uuid4
from models.ingestion import BatchDetails


class BatchTrackingService:
    def __init__(self, host: str = "localhost", port: int = 6379) -> None:
        self.redis_client: aioredis.Redis | None = None
        self.connection_details = (host, port)

    async def connect(self) -> None:
        """
        Establish the redis connection.
        """

        if not self.redis_client:
            self.redis_client = aioredis.Redis(
                host=self.connection_details[0],
                port=self.connection_details[1],
                db=1,
                decode_responses=True,
            )

        print("Redis Batch Tracking Service connected.")

    async def disconnect(self) -> None:
        """
        Disconnect the redis client.
        """

        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

        print("Redis Batch Tracking Service disconnected.")

    async def create_batch(self, total_files: int, user_id: str) -> str:
        """
        Initializes a new batch in Redis to track the processing status of uploaded files.
        """

        batch_id = str(uuid4())

        if not self.redis_client:
            await self.connect()
        if self.redis_client is not None:
            await self.redis_client.hset(
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

    async def increment_field(
        self,
        batch_id: str,
        field: Literal["files_chunked", "total_chunks", "chunks_embedded"],
        delta: int,
    ) -> None:
        """
        Increments a specific field in the batch hash by a given delta.
        """

        if not self.redis_client:
            await self.connect()
        if self.redis_client is not None:
            await self.redis_client.hincrby(f"batch:{batch_id}", field, delta)  # type: ignore

    async def update_status(
        self, batch_id: str, status: Literal["PENDING", "SUCCESS", "FAILED"]
    ) -> None:
        """
        Updates the status of the batch.
        """

        if not self.redis_client:
            await self.connect()
        if self.redis_client is not None:
            await self.redis_client.hset(f"batch:{batch_id}", "status", status)  # type: ignore

    async def get_batch_status(self, batch_id: str) -> BatchDetails | None:
        """
        Retrieves the current status of the batch.
        """

        if not self.redis_client:
            await self.connect()
        if self.redis_client is not None:
            batch_data = await self.redis_client.hgetall(f"batch:{batch_id}")  # type: ignore
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


async def check_ingestion_failure(batch_id: str) -> bool:
    """
    This function checks the current status of batch in redis hash and returns
    True if it is failed or missing, else False.
    """

    batch_details = await batch_tracking_service.get_batch_status(batch_id=batch_id)

    if batch_details is None:
        return True
    else:
        return batch_details.status == "FAILED" or batch_details.status == "NONE"


batch_tracking_service = BatchTrackingService()
