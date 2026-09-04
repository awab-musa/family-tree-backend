"""
Async SQLAlchemy engine + session factory for PostgreSQL (Amazon RDS).

NOTE for Lambda: the engine is created once at module import time and reused
across warm invocations. Keep DB_POOL_SIZE small since each Lambda execution
environment holds its own pool.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # avoids stale connections after RDS idle timeout
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a DB session and guarantees it closes."""
    async with AsyncSessionLocal() as session:
        yield session
