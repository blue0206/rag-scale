from ..db.s3 import s3_client


def cleanup_s3_batch(batch_id: str):
    """
    Deletes all files of a batch that were uploaded to S3.
    """

    try:
        s3_client.delete_batch(batch_id=batch_id, bucket="ragscale-uploads")
        print(f"Cleaned up S3 objects for batch {batch_id}")
    except Exception as e:
        print(f"Error during S3 cleanup for batch {batch_id}: {e}")
