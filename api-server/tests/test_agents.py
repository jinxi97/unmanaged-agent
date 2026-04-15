"""Tests for the agents router."""

import pytest


AGENT_PAYLOAD = {
    "name": "test-agent",
    "model": "claude-sonnet-4-6",
    "runtime": "pi-agent",
    "system_prompt": "You are a helpful assistant.",
}


@pytest.mark.anyio
async def test_create_agent(client):
    resp = await client.post("/agents", json=AGENT_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "test-agent"
    assert data["model"] == "claude-sonnet-4-6"
    assert data["runtime"] == "pi-agent"
    assert data["system_prompt"] == "You are a helpful assistant."
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_create_agent_defaults(client):
    resp = await client.post("/agents", json={"name": "minimal", "model": "gpt-4o"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["runtime"] == "pi-agent"
    assert data["system_prompt"] == ""


@pytest.mark.anyio
async def test_list_agents_empty(client):
    resp = await client.get("/agents")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_list_agents(client):
    await client.post("/agents", json=AGENT_PAYLOAD)
    await client.post("/agents", json={**AGENT_PAYLOAD, "name": "second-agent"})

    resp = await client.get("/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.anyio
async def test_get_agent(client):
    create_resp = await client.post("/agents", json=AGENT_PAYLOAD)
    agent_id = create_resp.json()["id"]

    resp = await client.get(f"/agents/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == agent_id
    assert resp.json()["name"] == "test-agent"


@pytest.mark.anyio
async def test_get_agent_not_found(client):
    resp = await client.get("/agents/nonexistent")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_delete_agent(client):
    create_resp = await client.post("/agents", json=AGENT_PAYLOAD)
    agent_id = create_resp.json()["id"]

    resp = await client.delete(f"/agents/{agent_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/agents/{agent_id}")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_delete_agent_not_found(client):
    resp = await client.delete("/agents/nonexistent")
    assert resp.status_code == 404
