import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.relationship import ParentChildSubtype, RelationshipType, SpouseStatus


class RelationshipCreate(BaseModel):
    tree_id: uuid.UUID
    relationship_type: RelationshipType
    person_a_id: uuid.UUID  # parent (if PARENT_CHILD)
    person_b_id: uuid.UUID  # child  (if PARENT_CHILD)

    parent_child_subtype: ParentChildSubtype | None = None
    spouse_status: SpouseStatus | None = None
    union_start_date: date | None = None
    union_end_date: date | None = None

    @model_validator(mode="after")
    def check_subtype_matches_type(self):
        if self.relationship_type == RelationshipType.PARENT_CHILD and not self.parent_child_subtype:
            raise ValueError("parent_child_subtype is required for parent_child relationships")
        if self.relationship_type == RelationshipType.SPOUSE and not self.spouse_status:
            raise ValueError("spouse_status is required for spouse relationships")
        return self


class RelationshipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tree_id: uuid.UUID
    relationship_type: RelationshipType
    person_a_id: uuid.UUID
    person_b_id: uuid.UUID
    parent_child_subtype: ParentChildSubtype | None = None
    spouse_status: SpouseStatus | None = None
    union_start_date: date | None = None
    union_end_date: date | None = None
    created_at: datetime
