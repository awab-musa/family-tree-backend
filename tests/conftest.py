"""
Shared pytest fixtures.

Uses an in-memory-style test DB via a separate DATABASE_URL (point this at a
disposable local/test Postgres instance - SQLite is NOT used since the app
relies on Postgres-specific features like recursive CTEs and ARRAY types).
"""
import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
