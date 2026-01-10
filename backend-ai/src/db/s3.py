import aioboto3
from ..core.config import env_config

s3_client = aioboto3.client(
    "s3",
    endpoint_url="https://minio:9000",
    aws_access_key_id=env_config["S3_ACCESS_KEY_ID"],
    aws_secret_access_key=env_config["S3_SECRET_ACCESS_KEY"],
    region_name="ap-south-1"
)
