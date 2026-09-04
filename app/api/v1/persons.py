import uuid

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.permissions import require_admin
from app.models.person import Person
from app.schemas.person import PersonCreate, PersonRead, PersonUpdate
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/persons", tags=["persons"])


@router.get("", response_model=list[PersonRead])
async def list_persons(tree_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    result = await db.execute(select(Person).where(Person.tree_id == tree_id))
    return result.scalars().all()


@router.get("/{person_id}", response_model=PersonRead)
async def get_person(person_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    person = await db.get(Person, person_id)
    if not person:
        raise NotFoundError("Person not found")
    return person


@router.post("", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
async def create_person(payload: PersonCreate, db: DbSession, current_user: CurrentUser):
    require_admin(current_user.role)
    person = Person(**payload.model_dump(), created_by=uuid.UUID(current_user.sub))
    db.add(person)
    await db.commit()
    await db.refresh(person)
    return person


@router.patch("/{person_id}", response_model=PersonRead)
async def update_person(
    person_id: uuid.UUID, payload: PersonUpdate, db: DbSession, current_user: CurrentUser
):
    require_admin(current_user.role)
    person = await db.get(Person, person_id)
    if not person:
        raise NotFoundError("Person not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(person, field, value)

    await db.commit()
    await db.refresh(person)
    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(person_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    require_admin(current_user.role)
    person = await db.get(Person, person_id)
    if not person:
        raise NotFoundError("Person not found")

    await db.delete(person)
    await db.commit()
