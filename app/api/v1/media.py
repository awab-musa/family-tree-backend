import uuid

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.permissions import require_admin
from app.models.media import Media
from app.models.person import Person
from app.schemas.media import (
    MediaRead,
    PresignedDownloadResponse,
    PresignedUploadRequest,
    PresignedUploadResponse,
)
from app.services import s3_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/presigned-upload", response_model=PresignedUploadResponse)
async def request_upload_url(payload: PresignedUploadRequest, db: DbSession, current_user: CurrentUser):
    require_admin(current_user.role)

    person = await db.get(Person, payload.person_id)
    if not person:
        raise NotFoundError("Person not found")

    s3_key = s3_service.build_object_key(person.tree_id, person.id, payload.file_name)
    upload_url = s3_service.generate_presigned_upload_url(s3_key, payload.content_type)

    media = Media(
        person_id=person.id,
        s3_key=s3_key,
        content_type=payload.content_type,
        uploaded_by=uuid.UUID(current_user.sub),
    )
    db.add(media)
    await db.commit()

    return PresignedUploadResponse(
        upload_url=upload_url,
        s3_key=s3_key,
        expires_in=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS,
    )


@router.get("/{media_id}/presigned-download", response_model=PresignedDownloadResponse)
async def request_download_url(media_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    media = await db.get(Media, media_id)
    if not media:
        raise NotFoundError("Media not found")

    download_url = s3_service.generate_presigned_download_url(media.s3_key)
    return PresignedDownloadResponse(
        download_url=download_url, expires_in=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS
    )


@router.get("/person/{person_id}", response_model=list[MediaRead])
async def list_media_for_person(person_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    result = await db.execute(select(Media).where(Media.person_id == person_id))
    return result.scalars().all()


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(media_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    require_admin(current_user.role)
    media = await db.get(Media, media_id)
    if not media:
        raise NotFoundError("Media not found")

    s3_service.delete_object(media.s3_key)
    await db.delete(media)
    await db.commit()
