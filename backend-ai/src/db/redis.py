from redis import Redis
from rq import Queue
from typing import List
from workers.chunking_worker import chunk_pdf
from workers.embedding_worker import process_chunks


class QueueService:
    def __init__(self, host: str = "localhost", port: int = 6379):
        self.queue_client: Redis | None = None
        self.connection_details = (host, port)
        self.chunking_queue: Queue | None = None
        self.embedding_queue: Queue | None = None

    def connect(self) -> None:
        """
        Establish redis connection and setup queues.
        """

        if not self.queue_client:
            self.queue_client = Redis(
                host=self.connection_details[0], port=self.connection_details[1], db=1
            )

            if not self.embedding_queue:
                self.embedding_queue = Queue(
                    name="embedding_queue",
                    connection=self.queue_client,
                )
            if not self.chunking_queue:
                self.chunking_queue = Queue(
                    name="chunking_queue", connection=self.queue_client
                )
        print("Redis Queue client connected.")

    def disconnect(self) -> None:
        """
        Disconnect the redis client and clear queues.
        """

        if self.queue_client:
            self.queue_client.close()
            self.queue_client = None
            self.chunking_queue = None
            self.embedding_queue = None

        print("Redis Queue client disconnected.")

    def enqueue_chunking_job(
        self, *, user_id: str, batch_id: str, object_key: str, bucket_name: str
    ):
        if not self.chunking_queue:
            self.connect()
        if self.chunking_queue is not None:
            self.chunking_queue.enqueue(
                chunk_pdf,
                {
                    "user_id": user_id,
                    "batch_id": batch_id,
                    "object_key": object_key,
                    "bucket_name": bucket_name,
                },
            )

    def enqueue_embedding_job(self, *, chunks: List):
        if not self.embedding_queue:
            self.connect()
        if self.embedding_queue is not None:
            self.embedding_queue.enqueue(process_chunks, chunks)


queue_service = QueueService()
