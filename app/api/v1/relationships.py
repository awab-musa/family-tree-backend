import uuid

from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.core.permissions import require_admin
from app.models.relationship import Relationship
from app.schemas.relationship import RelationshipCreate, RelationshipRead
from app.utils.exceptions import ConflictError, NotFoundError

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("", response_model=list[RelationshipRead])
async def list_relationships(tree_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    result = await db.execute(select(Relationship).where(Relationship.tree_id == tree_id))
    return result.scalars().all()


@router.post("", response_model=RelationshipRead, status_code=status.HTTP_201_CREATED)
async def create_relationship(payload: RelationshipCreate, db: DbSession, current_user: CurrentUser):
    require_admin(current_user.role)
    relationship = Relationship(**payload.model_dump())
    db.add(relationship)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("This relationship already exists or violates a constraint")
    await db.refresh(relationship)
    return relationship


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(relationship_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    require_admin(current_user.role)
    relationship = await db.get(Relationship, relationship_id)
    if not relationship:
        raise NotFoundError("Relationship not found")

    await db.delete(relationship)
    await db.commit()
