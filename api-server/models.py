"""Pydantic models for request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


# --- Agent ---


class AgentCreate(BaseModel):
    name: str
    model: str = Field(examples=["claude-sonnet-4-6"])
    runtime: str = Field(default="pi-agent", examples=["pi-agent"])
    system_prompt: str = ""


class AgentResponse(BaseModel):
    id: str
    name: str
    model: str
    runtime: str
    system_prompt: str
    created_at: datetime
    updated_at: datetime


# --- Environment ---


class EnvironmentCreate(BaseModel):
    name: str
    sandbox_provider: str = Field(examples=["e2b", "daytona"])
    config: dict = Field(default_factory=dict, examples=[{"packages": ["python3", "nodejs"], "network": {"outbound": True}}])


class EnvironmentResponse(BaseModel):
    id: str
    name: str
    sandbox_provider: str
    sandbox_id: str | None = None
    sandbox_url: str | None = None
    config: dict
    created_at: datetime
    updated_at: datetime


# --- Session ---


class SessionCreate(BaseModel):
    agent_id: str
    environment_id: str
    title: str = ""


class SessionResponse(BaseModel):
    id: str
    agent_id: str
    environment_id: str
    title: str
    created_at: datetime
    updated_at: datetime


# --- Event ---


class EventCreate(BaseModel):
    type: str = Field(examples=["message"])
    content: dict = Field(examples=[{"text": "Hello, agent!"}])


class EventResponse(BaseModel):
    id: str
    session_id: str
    type: str
    content: dict
    created_at: datetime
