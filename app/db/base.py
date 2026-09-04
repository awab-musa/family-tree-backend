"""
Declarative base for all ORM models.
Also acts as the single import point Alembic uses for autogeneration:
every model module must be imported here so `Base.metadata` knows about it.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models so they register themselves on Base.metadata.
# (placed at bottom to avoid circular imports)
from app.models import user, person, relationship, media  # noqa: E402,F401
