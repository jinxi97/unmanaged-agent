"""Tests for the Unmanaged Agent Python SDK."""

import json
from datetime import datetime, timezone

import httpx
import pytest

from unmanaged_agent import (
    Agent,
    AsyncUnmanagedAgentClient,
    Environment,
    Event,
    Session,
    UnmanagedAgentClient,
)

NOW = datetime.now(timezone.utc).isoformat()

AGENT_JSON = {
    "id": "agent-1",
    "name": "test-agent",
    "model": "claude-sonnet-4-6",
    "runtime": "pi-agent",
    "system_prompt": "You are helpful.",
    "created_at": NOW,
    "updated_at": NOW,
}

ENV_JSON = {
    "id": "env-1",
    "name": "test-env",
    "sandbox_provider": "e2b",
    "sandbox_id": "sandbox-123",
    "sandbox_url": "https://sandbox-123.e2b.dev",
    "config": {"packages": ["python3"]},
    "created_at": NOW,
    "updated_at": NOW,
}

SESSION_JSON = {
    "id": "session-1",
    "agent_id": "agent-1",
    "environment_id": "env-1",
    "title": "Test session",
    "created_at": NOW,
    "updated_at": NOW,
}

EVENT_JSON = {
    "id": "event-1",
    "session_id": "session-1",
    "type": "message",
    "content": {"text": "Hello!"},
    "created_at": NOW,
}


# --- Sync client tests ---


def test_create_agent(httpx_mock):
    httpx_mock.add_response(url="http://test/agents", json=AGENT_JSON, status_code=201)
    with UnmanagedAgentClient("http://test") as client:
        agent = client.agents.create(name="test-agent", model="claude-sonnet-4-6")
        assert isinstance(agent, Agent)
        assert agent.id == "agent-1"
        assert agent.name == "test-agent"


def test_list_agents(httpx_mock):
    httpx_mock.add_response(url="http://test/agents", json=[AGENT_JSON])
    with UnmanagedAgentClient("http://test") as client:
        agents = client.agents.list()
        assert len(agents) == 1
        assert agents[0].id == "agent-1"


def test_get_agent(httpx_mock):
    httpx_mock.add_response(url="http://test/agents/agent-1", json=AGENT_JSON)
    with UnmanagedAgentClient("http://test") as client:
        agent = client.agents.get("agent-1")
        assert agent.id == "agent-1"


def test_delete_agent(httpx_mock):
    httpx_mock.add_response(url="http://test/agents/agent-1", status_code=204)
    with UnmanagedAgentClient("http://test") as client:
        client.agents.delete("agent-1")  # Should not raise


def test_create_environment(httpx_mock):
    httpx_mock.add_response(url="http://test/environments", json=ENV_JSON, status_code=201)
    with UnmanagedAgentClient("http://test") as client:
        env = client.environments.create(name="test-env", sandbox_provider="e2b")
        assert isinstance(env, Environment)
        assert env.sandbox_id == "sandbox-123"


def test_list_environments(httpx_mock):
    httpx_mock.add_response(url="http://test/environments", json=[ENV_JSON])
    with UnmanagedAgentClient("http://test") as client:
        envs = client.environments.list()
        assert len(envs) == 1


def test_create_session(httpx_mock):
    httpx_mock.add_response(url="http://test/sessions", json=SESSION_JSON, status_code=201)
    with UnmanagedAgentClient("http://test") as client:
        session = client.sessions.create(agent_id="agent-1", environment_id="env-1", title="Test session")
        assert isinstance(session, Session)
        assert session.agent_id == "agent-1"


def test_list_sessions(httpx_mock):
    httpx_mock.add_response(url="http://test/sessions", json=[SESSION_JSON])
    with UnmanagedAgentClient("http://test") as client:
        sessions = client.sessions.list()
        assert len(sessions) == 1


def test_get_session(httpx_mock):
    httpx_mock.add_response(url="http://test/sessions/session-1", json=SESSION_JSON)
    with UnmanagedAgentClient("http://test") as client:
        session = client.sessions.get("session-1")
        assert session.title == "Test session"


def test_list_events(httpx_mock):
    httpx_mock.add_response(url="http://test/sessions/session-1/events", json=[EVENT_JSON])
    with UnmanagedAgentClient("http://test") as client:
        events = client.sessions.list_events("session-1")
        assert len(events) == 1
        assert isinstance(events[0], Event)
        assert events[0].content == {"text": "Hello!"}


# --- Async client tests ---


@pytest.mark.asyncio
async def test_async_create_agent(httpx_mock):
    httpx_mock.add_response(url="http://test/agents", json=AGENT_JSON, status_code=201)
    async with AsyncUnmanagedAgentClient("http://test") as client:
        agent = await client.agents.create(name="test-agent", model="claude-sonnet-4-6")
        assert isinstance(agent, Agent)
        assert agent.id == "agent-1"


@pytest.mark.asyncio
async def test_async_list_agents(httpx_mock):
    httpx_mock.add_response(url="http://test/agents", json=[AGENT_JSON])
    async with AsyncUnmanagedAgentClient("http://test") as client:
        agents = await client.agents.list()
        assert len(agents) == 1


@pytest.mark.asyncio
async def test_async_list_events(httpx_mock):
    httpx_mock.add_response(url="http://test/sessions/session-1/events", json=[EVENT_JSON])
    async with AsyncUnmanagedAgentClient("http://test") as client:
        events = await client.sessions.list_events("session-1")
        assert len(events) == 1
        assert events[0].type == "message"
