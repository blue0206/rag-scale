from fastapi import APIRouter, UploadFile, File, Depends
from typing import List
from ...core.dependencies import get_current_user
from ...db.s3 import s3_client
from ...services.batch_tracking_service import batch_tracking_service
from ...services.queue_service import queue_service
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
        batch_id = await batch_tracking_service.create_batch(len(files), user_id=user_id)

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
            }
        )
    except Exception:
        return ApiResponse(
            success=False,
            status_code=500,
            payload="Internal Server Error"
        )
