"""Shared test fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

from database import SCHEMA, get_db
from main import app

import aiosqlite


@pytest.fixture
async def db():
    """In-memory SQLite database for tests."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.executescript(SCHEMA)
    await conn.commit()
    try:
        yield conn
    finally:
        await conn.close()


@pytest.fixture
async def client(db):
    """Test client with the in-memory database injected."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
