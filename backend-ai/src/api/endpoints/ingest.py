import asyncio
import json
from fastapi import APIRouter, UploadFile, File, Depends, Request
from fastapi.responses import StreamingResponse
from typing import List
from pydantic import ValidationError
from models.ingestion import ProgressState
from ...core.dependencies import get_current_user
from ...db.s3 import s3_client
from ...services.batch_tracking_service import batch_tracking_service
from ...services.queue_service import queue_service
from ...services.pubsub_service import pubsub_service
from ...models.api import ApiResponse

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...), user_id: str = Depends(get_current_user)
):
    """
    Uploads files to S3 and enqueues chunking jobs.
    """

    try:
        batch_id = await batch_tracking_service.create_batch(
            len(files), user_id=user_id
        )

        for file in files:
            file_content = await file.read()
            async with s3_client:
                await s3_client.put_object(
                    Bucket="ragscale-uploads",
                    Key=f"{batch_id}/{file.filename}",
                    Body=file_content,
                )

            queue_service.enqueue_chunking_job(
                user_id=user_id,
                batch_id=batch_id,
                object_key=f"{batch_id}/{file.filename}",
                bucket_name="ragscale-uploads",
            )

        return ApiResponse(
            success=True,
            status_code=202,
            payload={
                "message": "Files uploaded and ingestion jobs enqueued.",
                "batch_id": batch_id,
            },
        )
    except Exception:
        return ApiResponse(
            success=False, status_code=500, payload="Internal Server Error"
        )


@router.get("/status/{batch_id}")
async def get_ingestion_status(req: Request, batch_id: str) -> StreamingResponse | None:
    """
    Sends batch status updates to clients as server-sent events.
    """

    async def ingestion_event_handler():
        """
        This function setups up a generator function that subscribes and listens to the redis
        channel for the batch and streams the updates to the client via SSE.

        Before subscribing, the function first gets current progress directly from hash and returns
        the progress as first event. If the status is already "SUCCESS", the function simply returns
        and the connection is closed. Else, the connection is set up and the messages are parsed
        using pydantic and yielded.
        """

        # First we check for the current status in Redis hash and return the result.
        # This is useful in case the ingestion is over before this endpoint is requested.
        current_status = await batch_tracking_service.get_batch_status(
            batch_id=batch_id
        )
        if current_status is not None:
            data = ProgressState(
                details=None,
                user_id=current_status.user_id,
                status=current_status.status
                if current_status.status != "NONE"
                else "PENDING",
                progress=int(
                    (current_status.chunks_embedded / current_status.total_chunks) * 100
                )
                if current_status.total_chunks != 0
                else 0,
            )
            # Send the first event.
            yield f"data: {json.dumps(data)}\n\n"

            # If the batch process already finished, return. No more streaming required.
            if current_status.status == "SUCCESS":
                return

        channel = f"status:{batch_id}"
        listener = pubsub_service.subscribe(channel)

        try:
            while not await req.is_disconnected():
                async for message in listener:
                    try:
                        data = ProgressState.model_validate_json(message)

                        # Send the progress back to client.
                        yield f"data: {data.model_dump_json()}\n\n"

                        # Close if failed or finished.
                        if data.status == "FAILED" or data.status == "SUCCESS":
                            return
                    except ValidationError as e:
                        print(f"Received invalid prgress state: {str(e)}")
                        continue

                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            print(f"Client disconnected from batch: {batch_id}")

    return StreamingResponse(ingestion_event_handler(), media_type="text/event-stream")
