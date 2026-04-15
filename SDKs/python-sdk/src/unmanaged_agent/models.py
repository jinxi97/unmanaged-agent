"""Data models for the Unmanaged Agent API."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Agent:
    id: str
    name: str
    model: str
    runtime: str
    system_prompt: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Environment:
    id: str
    name: str
    sandbox_provider: str
    config: dict
    created_at: datetime
    updated_at: datetime
    sandbox_id: str | None = None
    sandbox_url: str | None = None


@dataclass
class Session:
    id: str
    agent_id: str
    environment_id: str
    title: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Event:
    id: str
    session_id: str
    type: str
    content: dict
    created_at: datetime
