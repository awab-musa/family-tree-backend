"""
S3 presigned URL generation for direct browser upload/download.
The backend never proxies file bytes - it only issues short-lived signed URLs.
"""
import uuid

import boto3
from botocore.config import Config

from app.core.config import settings

_s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    config=Config(signature_version="s3v4"),
)


def build_object_key(tree_id: uuid.UUID, person_id: uuid.UUID, file_name: str) -> str:
    ext = file_name.rsplit(".", 1)[-1] if "." in file_name else "bin"
    unique_name = f"{uuid.uuid4()}.{ext}"
    return f"trees/{tree_id}/persons/{person_id}/{unique_name}"


def generate_presigned_upload_url(s3_key: str, content_type: str) -> str:
    return _s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": s3_key,
            "ContentType": content_type,
        },
        ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS,
    )


def generate_presigned_download_url(s3_key: str) -> str:
    return _s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS,
    )


def delete_object(s3_key: str) -> None:
    _s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
