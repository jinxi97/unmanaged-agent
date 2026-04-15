"""Session CRUD + event streaming endpoints."""

import json
import uuid
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from database import get_db
from models import EventCreate, EventResponse, SessionCreate, SessionResponse
from services.agent_runtime import run_agent

router = APIRouter(prefix="/sessions", tags=["session"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(body: SessionCreate, db: aiosqlite.Connection = Depends(get_db)):
    # Verify agent and environment exist
    cursor = await db.execute("SELECT id FROM agents WHERE id = ?", (body.agent_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Agent not found")

    cursor = await db.execute("SELECT id FROM environments WHERE id = ?", (body.environment_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Environment not found")

    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO sessions (id, agent_id, environment_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, body.agent_id, body.environment_id, body.title, now, now),
    )
    await db.commit()
    return SessionResponse(
        id=session_id,
        agent_id=body.agent_id,
        environment_id=body.environment_id,
        title=body.title,
        created_at=now,
        updated_at=now,
    )


@router.get("", response_model=list[SessionResponse])
async def list_sessions(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT * FROM sessions ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [SessionResponse(**dict(row)) for row in rows]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**dict(row))


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM events WHERE session_id = ?", (session_id,))
    cursor = await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/events")
async def send_event(session_id: str, body: EventCreate, db: aiosqlite.Connection = Depends(get_db)):
    """Send an event to the session and stream back agent responses via SSE."""
    # Look up session, agent, and environment
    cursor = await db.execute(
        """SELECT s.*, a.model, a.runtime, a.system_prompt,
                  e.sandbox_id
           FROM sessions s
           JOIN agents a ON s.agent_id = a.id
           JOIN environments e ON s.environment_id = e.id
           WHERE s.id = ?""",
        (session_id,),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = dict(row)

    # Persist the incoming event
    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO events (id, session_id, type, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (event_id, session_id, body.type, json.dumps(body.content), now),
    )
    await db.commit()

    # Extract message text from the event content
    message = body.content.get("text", json.dumps(body.content))

    async def event_generator():
        # Stream agent responses using the environment's sandbox
        async for event in run_agent(
            runtime=session_data["runtime"],
            model=session_data["model"],
            system_prompt=session_data["system_prompt"],
            message=message,
            sandbox_id=session_data["sandbox_id"],
        ):
            # Persist each agent event
            resp_event_id = str(uuid.uuid4())
            resp_now = datetime.now(timezone.utc).isoformat()
            async with aiosqlite.connect("unmanaged_agent.db") as event_db:
                await event_db.execute(
                    "INSERT INTO events (id, session_id, type, content, created_at) VALUES (?, ?, ?, ?, ?)",
                    (resp_event_id, session_id, event.get("type", "unknown"), json.dumps(event.get("content", {})), resp_now),
                )
                await event_db.commit()

            yield {"event": event.get("type", "message"), "data": json.dumps(event)}

    return EventSourceResponse(event_generator())


@router.get("/{session_id}/events", response_model=list[EventResponse])
async def list_events(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Fetch the full event history for a session."""
    cursor = await db.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Session not found")

    cursor = await db.execute(
        "SELECT * FROM events WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    )
    rows = await cursor.fetchall()
    results = []
    for row in rows:
        data = dict(row)
        data["content"] = json.loads(data["content"])
        results.append(EventResponse(**data))
    return results
