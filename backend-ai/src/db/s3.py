import asyncio
import boto3
from types_boto3_s3 import S3Client
from ..core.config import env_config


class S3Service:
    def __init__(self) -> None:
        self.client: S3Client | None = None

    def connect(self) -> None:
        """
        Connects the S3 client.
        """

        self.client = boto3.client(
            "s3",
            endpoint_url="https://minio:9000",
            aws_access_key_id=env_config.S3_ACCESS_KEY_ID,
            aws_secret_access_key=env_config.S3_SECRET_ACCESS_KEY,
            region_name="ap-south-1",
        )

        print("S3 Client connected.")

    def disconnect(self) -> None:
        """
        Disconnects the S3 client.
        """

        if self.client:
            self.client.close()
            self.client = None

            print("S3 client disconnected.")
    
    async def upload_file_async(self, bucket: str, key: str, file: bytes) -> None:
        """
        Uploads file in memory to S3 on a separate thread.
        """
        if not self.client:
            self.connect()
        if self.client is not None:
            await asyncio.to_thread(
                self.client.put_object, 
                Bucket=bucket,
                Key=key,
                Body=file
            )

    async def download_file_async(self, bucket: str, key: str, path: str) -> None:
        """
        Downloads a file from S3 to a local path on a separate thread.
        """

        if not self.client:
            self.connect()
        if self.client is not None:
            await asyncio.to_thread(
                self.client.download_file,
                Bucket=bucket,
                Key=key,
                Filename=path
            )
    
    async def delete_file_async(self, bucket: str, key: str) -> None:
        """
        Deletes the file with a given key from S3 storage on a separate thread.
        """

        if not self.client:
            self.connect()
        if self.client is not None:
            await asyncio.to_thread(
                self.client.delete_object,
                Bucket=bucket,
                Key=key
            )

    async def create_presigned_url(self, bucket: str, key: str, expiry: int = 3600) -> str:
        """
        Generates a presigned url in a separate thread.
        """

        url = ""
        if not self.client:
            self.connect()
        if self.client is not None:
            url = await asyncio.to_thread(
                self.client.generate_presigned_url,
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiry
            )

        return url

s3_client = S3Service()
