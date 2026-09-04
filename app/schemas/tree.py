"""
Response shape optimized for react-d3-tree / D3.js consumption on the frontend.
"""
import uuid

from pydantic import BaseModel

from app.schemas.person import PersonRead


class TreeNode(BaseModel):
    person: PersonRead
    children: list["TreeNode"] = []
    spouses: list[PersonRead] = []


TreeNode.model_rebuild()


class AncestryPathNode(BaseModel):
    person: PersonRead
    generation: int  # 0 = root person, 1 = parents, 2 = grandparents, ...
    relation_subtype: str | None = None
