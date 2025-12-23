
import boto3
from api.config import settings

def get_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )

def upload_file(local_path: str, key: str) -> str:
    client = get_client()
    client.upload_file(local_path, settings.r2_bucket_name, key)
    return f"{settings.r2_endpoint}/{settings.r2_bucket_name}/{key}"