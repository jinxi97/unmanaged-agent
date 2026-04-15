"""Sync and async clients for the Unmanaged Agent API."""

from __future__ import annotations

import json
from collections.abc import Iterator, AsyncIterator
from datetime import datetime
from typing import Any

import httpx

from unmanaged_agent.models import Agent, Environment, Session, Event


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _to_agent(data: dict) -> Agent:
    return Agent(
        id=data["id"],
        name=data["name"],
        model=data["model"],
        runtime=data["runtime"],
        system_prompt=data["system_prompt"],
        created_at=_parse_datetime(data["created_at"]),
        updated_at=_parse_datetime(data["updated_at"]),
    )


def _to_environment(data: dict) -> Environment:
    return Environment(
        id=data["id"],
        name=data["name"],
        sandbox_provider=data["sandbox_provider"],
        sandbox_id=data.get("sandbox_id"),
        sandbox_url=data.get("sandbox_url"),
        config=data["config"],
        created_at=_parse_datetime(data["created_at"]),
        updated_at=_parse_datetime(data["updated_at"]),
    )


def _to_session(data: dict) -> Session:
    return Session(
        id=data["id"],
        agent_id=data["agent_id"],
        environment_id=data["environment_id"],
        title=data["title"],
        created_at=_parse_datetime(data["created_at"]),
        updated_at=_parse_datetime(data["updated_at"]),
    )


def _to_event(data: dict) -> Event:
    return Event(
        id=data["id"],
        session_id=data["session_id"],
        type=data["type"],
        content=data["content"],
        created_at=_parse_datetime(data["created_at"]),
    )


def _parse_sse_events(text: str) -> Iterator[dict]:
    """Parse SSE text into event dicts."""
    event_type = None
    for line in text.splitlines():
        if line.startswith("event: "):
            event_type = line[7:]
        elif line.startswith("data: "):
            data = line[6:]
            try:
                yield {"event": event_type, "data": json.loads(data)}
            except json.JSONDecodeError:
                yield {"event": event_type, "data": data}
            event_type = None


# --- Resource namespaces ---


class AgentsResource:
    """Agents API."""

    def __init__(self, http: httpx.Client):
        self._http = http

    def create(
        self,
        name: str,
        model: str,
        runtime: str = "pi-agent",
        system_prompt: str = "",
    ) -> Agent:
        """Create a new agent."""
        resp = self._http.post(
            "/agents",
            json={"name": name, "model": model, "runtime": runtime, "system_prompt": system_prompt},
        )
        resp.raise_for_status()
        return _to_agent(resp.json())

    def list(self) -> list[Agent]:
        """List all agents."""
        resp = self._http.get("/agents")
        resp.raise_for_status()
        return [_to_agent(a) for a in resp.json()]

    def get(self, agent_id: str) -> Agent:
        """Get an agent by ID."""
        resp = self._http.get(f"/agents/{agent_id}")
        resp.raise_for_status()
        return _to_agent(resp.json())

    def delete(self, agent_id: str) -> None:
        """Delete an agent by ID."""
        resp = self._http.delete(f"/agents/{agent_id}")
        resp.raise_for_status()


class EnvironmentsResource:
    """Environments API."""

    def __init__(self, http: httpx.Client):
        self._http = http

    def create(
        self,
        name: str,
        sandbox_provider: str,
        config: dict | None = None,
    ) -> Environment:
        """Create a new environment and provision its sandbox."""
        resp = self._http.post(
            "/environments",
            json={"name": name, "sandbox_provider": sandbox_provider, "config": config or {}},
            timeout=300.0,
        )
        resp.raise_for_status()
        return _to_environment(resp.json())

    def list(self) -> list[Environment]:
        """List all environments."""
        resp = self._http.get("/environments")
        resp.raise_for_status()
        return [_to_environment(e) for e in resp.json()]

    def get(self, environment_id: str) -> Environment:
        """Get an environment by ID."""
        resp = self._http.get(f"/environments/{environment_id}")
        resp.raise_for_status()
        return _to_environment(resp.json())

    def delete(self, environment_id: str) -> None:
        """Delete an environment and tear down its sandbox."""
        resp = self._http.delete(f"/environments/{environment_id}")
        resp.raise_for_status()


class SessionsResource:
    """Sessions API."""

    def __init__(self, http: httpx.Client):
        self._http = http

    def create(
        self,
        agent_id: str,
        environment_id: str,
        title: str = "",
    ) -> Session:
        """Create a new session."""
        resp = self._http.post(
            "/sessions",
            json={"agent_id": agent_id, "environment_id": environment_id, "title": title},
        )
        resp.raise_for_status()
        return _to_session(resp.json())

    def list(self) -> list[Session]:
        """List all sessions."""
        resp = self._http.get("/sessions")
        resp.raise_for_status()
        return [_to_session(s) for s in resp.json()]

    def get(self, session_id: str) -> Session:
        """Get a session by ID."""
        resp = self._http.get(f"/sessions/{session_id}")
        resp.raise_for_status()
        return _to_session(resp.json())

    def delete(self, session_id: str) -> None:
        """Delete a session."""
        resp = self._http.delete(f"/sessions/{session_id}")
        resp.raise_for_status()

    def send_event(
        self,
        session_id: str,
        type: str = "message",
        content: dict | None = None,
    ) -> Iterator[dict]:
        """Send an event and stream back SSE responses."""
        with self._http.stream(
            "POST",
            f"/sessions/{session_id}/events",
            json={"type": type, "content": content or {}},
            timeout=300.0,
        ) as resp:
            resp.raise_for_status()
            event_type = None
            for line in resp.iter_lines():
                if line.startswith("event: "):
                    event_type = line[7:]
                elif line.startswith("data: "):
                    data = line[6:]
                    try:
                        yield {"event": event_type, "data": json.loads(data)}
                    except json.JSONDecodeError:
                        yield {"event": event_type, "data": data}
                    event_type = None

    def list_events(self, session_id: str) -> list[Event]:
        """Fetch the full event history for a session."""
        resp = self._http.get(f"/sessions/{session_id}/events")
        resp.raise_for_status()
        return [_to_event(e) for e in resp.json()]


# --- Async resource namespaces ---


class AsyncAgentsResource:
    """Async Agents API."""

    def __init__(self, http: httpx.AsyncClient):
        self._http = http

    async def create(
        self,
        name: str,
        model: str,
        runtime: str = "pi-agent",
        system_prompt: str = "",
    ) -> Agent:
        """Create a new agent."""
        resp = await self._http.post(
            "/agents",
            json={"name": name, "model": model, "runtime": runtime, "system_prompt": system_prompt},
        )
        resp.raise_for_status()
        return _to_agent(resp.json())

    async def list(self) -> list[Agent]:
        """List all agents."""
        resp = await self._http.get("/agents")
        resp.raise_for_status()
        return [_to_agent(a) for a in resp.json()]

    async def get(self, agent_id: str) -> Agent:
        """Get an agent by ID."""
        resp = await self._http.get(f"/agents/{agent_id}")
        resp.raise_for_status()
        return _to_agent(resp.json())

    async def delete(self, agent_id: str) -> None:
        """Delete an agent by ID."""
        resp = await self._http.delete(f"/agents/{agent_id}")
        resp.raise_for_status()


class AsyncEnvironmentsResource:
    """Async Environments API."""

    def __init__(self, http: httpx.AsyncClient):
        self._http = http

    async def create(
        self,
        name: str,
        sandbox_provider: str,
        config: dict | None = None,
    ) -> Environment:
        """Create a new environment and provision its sandbox."""
        resp = await self._http.post(
            "/environments",
            json={"name": name, "sandbox_provider": sandbox_provider, "config": config or {}},
            timeout=300.0,
        )
        resp.raise_for_status()
        return _to_environment(resp.json())

    async def list(self) -> list[Environment]:
        """List all environments."""
        resp = await self._http.get("/environments")
        resp.raise_for_status()
        return [_to_environment(e) for e in resp.json()]

    async def get(self, environment_id: str) -> Environment:
        """Get an environment by ID."""
        resp = await self._http.get(f"/environments/{environment_id}")
        resp.raise_for_status()
        return _to_environment(resp.json())

    async def delete(self, environment_id: str) -> None:
        """Delete an environment and tear down its sandbox."""
        resp = await self._http.delete(f"/environments/{environment_id}")
        resp.raise_for_status()


class AsyncSessionsResource:
    """Async Sessions API."""

    def __init__(self, http: httpx.AsyncClient):
        self._http = http

    async def create(
        self,
        agent_id: str,
        environment_id: str,
        title: str = "",
    ) -> Session:
        """Create a new session."""
        resp = await self._http.post(
            "/sessions",
            json={"agent_id": agent_id, "environment_id": environment_id, "title": title},
        )
        resp.raise_for_status()
        return _to_session(resp.json())

    async def list(self) -> list[Session]:
        """List all sessions."""
        resp = await self._http.get("/sessions")
        resp.raise_for_status()
        return [_to_session(s) for s in resp.json()]

    async def get(self, session_id: str) -> Session:
        """Get a session by ID."""
        resp = await self._http.get(f"/sessions/{session_id}")
        resp.raise_for_status()
        return _to_session(resp.json())

    async def delete(self, session_id: str) -> None:
        """Delete a session."""
        resp = await self._http.delete(f"/sessions/{session_id}")
        resp.raise_for_status()

    async def send_event(
        self,
        session_id: str,
        type: str = "message",
        content: dict | None = None,
    ) -> AsyncIterator[dict]:
        """Send an event and stream back SSE responses."""
        async with self._http.stream(
            "POST",
            f"/sessions/{session_id}/events",
            json={"type": type, "content": content or {}},
            timeout=300.0,
        ) as resp:
            resp.raise_for_status()
            event_type = None
            async for line in resp.aiter_lines():
                if line.startswith("event: "):
                    event_type = line[7:]
                elif line.startswith("data: "):
                    data = line[6:]
                    try:
                        yield {"event": event_type, "data": json.loads(data)}
                    except json.JSONDecodeError:
                        yield {"event": event_type, "data": data}
                    event_type = None

    async def list_events(self, session_id: str) -> list[Event]:
        """Fetch the full event history for a session."""
        resp = await self._http.get(f"/sessions/{session_id}/events")
        resp.raise_for_status()
        return [_to_event(e) for e in resp.json()]


# --- Top-level clients ---


class UnmanagedAgentClient:
    """Sync client for the Unmanaged Agent API.

    Usage:
        client = UnmanagedAgentClient("http://localhost:8000")
        agent = client.agents.create(name="my-agent", model="claude-sonnet-4-6")
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self._http = httpx.Client(base_url=base_url)
        self.agents = AgentsResource(self._http)
        self.environments = EnvironmentsResource(self._http)
        self.sessions = SessionsResource(self._http)

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AsyncUnmanagedAgentClient:
    """Async client for the Unmanaged Agent API.

    Usage:
        async with AsyncUnmanagedAgentClient("http://localhost:8000") as client:
            agent = await client.agents.create(name="my-agent", model="claude-sonnet-4-6")
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self._http = httpx.AsyncClient(base_url=base_url)
        self.agents = AsyncAgentsResource(self._http)
        self.environments = AsyncEnvironmentsResource(self._http)
        self.sessions = AsyncSessionsResource(self._http)

    async def close(self):
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
