"""
Relationship edges between persons.

Family trees are NOT strict hierarchical trees (remarriage, adoption, and
multiple parent-sets create cross-links), so we model relationships as
explicit edges rather than a single parent_id column on Person. This is
also what makes recursive CTE ancestor/descendant traversal correct.

Two edge types are modeled:
  - PARENT_CHILD: directed edge, parent_id -> child_id
  - SPOUSE:       undirected-in-practice edge, person_a_id <-> person_b_id

`relation_subtype` on PARENT_CHILD distinguishes biological / adoptive / step,
so the UI and GEDCOM-style exports can render them differently.
"""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RelationshipType(str, enum.Enum):
    PARENT_CHILD = "parent_child"
    SPOUSE = "spouse"


class ParentChildSubtype(str, enum.Enum):
    BIOLOGICAL = "biological"
    ADOPTIVE = "adoptive"
    STEP = "step"
    FOSTER = "foster"


class SpouseStatus(str, enum.Enum):
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    PARTNERED = "partnered"  # unmarried partnership


class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        # Prevent a duplicate identical edge between the same two people of the same type.
        UniqueConstraint(
            "person_a_id", "person_b_id", "relationship_type", name="uq_relationship_edge"
        ),
        # A person cannot be their own parent/spouse.
        CheckConstraint("person_a_id != person_b_id", name="ck_no_self_relationship"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, name="relationship_type_enum"), nullable=False
    )

    # For PARENT_CHILD: person_a_id = parent, person_b_id = child.
    # For SPOUSE:       person_a_id / person_b_id order is arbitrary.
    person_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Only meaningful when relationship_type == PARENT_CHILD.
    parent_child_subtype: Mapped[ParentChildSubtype | None] = mapped_column(
        Enum(ParentChildSubtype, name="parent_child_subtype_enum"), nullable=True
    )

    # Only meaningful when relationship_type == SPOUSE.
    spouse_status: Mapped[SpouseStatus | None] = mapped_column(
        Enum(SpouseStatus, name="spouse_status_enum"), nullable=True
    )
    union_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # marriage date
    union_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # divorce/death date

    tree_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
