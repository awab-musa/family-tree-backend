"""
Person table - a single node in the family tree.
Gender/dates are optional since historical records are often incomplete.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.db.base import Base


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    maiden_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # "male" | "female" | "other" | "unknown"
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)

    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    death_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    birth_place: Mapped[str | None] = mapped_column(String(255), nullable=True)

    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Denormalized pointer to the primary profile photo (S3 key), for quick tree rendering.
    profile_photo_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Owning tree/root reference - lets multiple family trees live in one DB.
    tree_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    media_items: Mapped[list["Media"]] = orm_relationship(
        "Media", back_populates="person", cascade="all, delete-orphan"
    )
