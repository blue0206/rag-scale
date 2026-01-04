from redis import Redis
from rq import Queue

redis_client = Redis(
    host="localhost",
    port=6379
)

chunking_queue = Queue(
    name="chunking_queue",
    connection=redis_client
)

query_queue = Queue(
    name="query_queue",
    connection=redis_client
)
