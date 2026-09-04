import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.tree import AncestryPathNode, TreeNode
from app.services import tree_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/tree", tags=["tree"])


@router.get("/{person_id}/ancestors", response_model=list[AncestryPathNode])
async def get_ancestors(person_id: uuid.UUID, tree_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    return await tree_service.get_ancestors(db, person_id, tree_id)


@router.get("/{person_id}/descendants", response_model=list[AncestryPathNode])
async def get_descendants(person_id: uuid.UUID, tree_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    return await tree_service.get_descendants(db, person_id, tree_id)


@router.get("/{person_id}/nested", response_model=TreeNode)
async def get_nested_tree(person_id: uuid.UUID, tree_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    node = await tree_service.build_nested_tree(db, person_id, tree_id)
    if not node:
        raise NotFoundError("Person not found")
    return node
