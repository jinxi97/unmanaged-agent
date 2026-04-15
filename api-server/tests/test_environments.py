"""Tests for the environments router."""

from unittest.mock import AsyncMock, patch

import pytest


ENV_PAYLOAD = {
    "name": "python-sandbox",
    "sandbox_provider": "e2b",
    "config": {"packages": ["python3", "nodejs"], "network": {"outbound": True}},
}

MOCK_SANDBOX_INFO = {
    "sandbox_id": "sandbox-123",
    "url": "https://sandbox-123.e2b.dev",
    "provider": "e2b",
}


@pytest.fixture(autouse=True)
def mock_sandbox():
    with (
        patch("routers.environments.create_sandbox", new_callable=AsyncMock, return_value=MOCK_SANDBOX_INFO) as mock_create,
        patch("routers.environments.destroy_sandbox", new_callable=AsyncMock) as mock_destroy,
    ):
        yield mock_create, mock_destroy


@pytest.mark.anyio
async def test_create_environment(client):
    resp = await client.post("/environments", json=ENV_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "python-sandbox"
    assert data["sandbox_provider"] == "e2b"
    assert data["sandbox_id"] == "sandbox-123"
    assert data["sandbox_url"] == "https://sandbox-123.e2b.dev"
    assert data["config"] == ENV_PAYLOAD["config"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_create_environment_provisions_sandbox(client, mock_sandbox):
    mock_create, _ = mock_sandbox
    await client.post("/environments", json=ENV_PAYLOAD)
    mock_create.assert_called_once_with("e2b", ENV_PAYLOAD["config"])


@pytest.mark.anyio
async def test_list_environments_empty(client):
    resp = await client.get("/environments")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_list_environments(client):
    await client.post("/environments", json=ENV_PAYLOAD)
    await client.post("/environments", json={**ENV_PAYLOAD, "name": "go-sandbox"})

    resp = await client.get("/environments")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.anyio
async def test_get_environment(client):
    create_resp = await client.post("/environments", json=ENV_PAYLOAD)
    env_id = create_resp.json()["id"]

    resp = await client.get(f"/environments/{env_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == env_id
    assert resp.json()["name"] == "python-sandbox"


@pytest.mark.anyio
async def test_get_environment_not_found(client):
    resp = await client.get("/environments/nonexistent")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_delete_environment(client, mock_sandbox):
    _, mock_destroy = mock_sandbox
    create_resp = await client.post("/environments", json=ENV_PAYLOAD)
    env_id = create_resp.json()["id"]

    resp = await client.delete(f"/environments/{env_id}")
    assert resp.status_code == 204
    mock_destroy.assert_called_once_with("e2b", "sandbox-123")

    resp = await client.get(f"/environments/{env_id}")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_delete_environment_not_found(client):
    resp = await client.delete("/environments/nonexistent")
    assert resp.status_code == 404
