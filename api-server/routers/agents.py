"""Agent CRUD endpoints."""

import json
import uuid
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from models import AgentCreate, AgentResponse

router = APIRouter(prefix="/agents", tags=["agent"])


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(body: AgentCreate, db: aiosqlite.Connection = Depends(get_db)):
    """Create a new agent with the given name, model, runtime, and system prompt."""
    agent_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO agents (id, name, model, runtime, system_prompt, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (agent_id, body.name, body.model, body.runtime, body.system_prompt, now, now),
    )
    await db.commit()
    return AgentResponse(
        id=agent_id,
        name=body.name,
        model=body.model,
        runtime=body.runtime,
        system_prompt=body.system_prompt,
        created_at=now,
        updated_at=now,
    )


@router.get("", response_model=list[AgentResponse])
async def list_agents(db: aiosqlite.Connection = Depends(get_db)):
    """List all agents, ordered by most recently created first."""
    cursor = await db.execute("SELECT * FROM agents ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [AgentResponse(**dict(row)) for row in rows]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get an agent by ID. Returns 404 if not found."""
    cursor = await db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(**dict(row))


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Delete an agent by ID. Returns 404 if not found."""
    cursor = await db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
