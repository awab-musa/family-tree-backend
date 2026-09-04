import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PresignedUploadRequest(BaseModel):
    person_id: uuid.UUID
    file_name: str
    content_type: str  # e.g. "image/jpeg"


class PresignedUploadResponse(BaseModel):
    upload_url: str  # PUT this file's bytes here
    s3_key: str
    expires_in: int


class PresignedDownloadResponse(BaseModel):
    download_url: str
    expires_in: int


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    person_id: uuid.UUID
    s3_key: str
    content_type: str
    file_size_bytes: int | None = None
    caption: str | None = None
    created_at: datetime
