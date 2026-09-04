import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PersonBase(BaseModel):
    first_name: str
    last_name: str | None = None
    maiden_name: str | None = None
    gender: str | None = None  # male | female | other | unknown
    birth_date: date | None = None
    death_date: date | None = None
    birth_place: str | None = None
    bio: str | None = None


class PersonCreate(PersonBase):
    tree_id: uuid.UUID


class PersonUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    maiden_name: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    death_date: date | None = None
    birth_place: str | None = None
    bio: str | None = None
    profile_photo_key: str | None = None


class PersonRead(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tree_id: uuid.UUID
    profile_photo_key: str | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
