"""Environment CRUD endpoints."""

import json
import uuid
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from models import EnvironmentCreate, EnvironmentResponse
from services.sandbox import create_sandbox, destroy_sandbox

router = APIRouter(prefix="/environments", tags=["environment"])


def _row_to_response(row: aiosqlite.Row) -> EnvironmentResponse:
    data = dict(row)
    data["config"] = json.loads(data["config"])
    return EnvironmentResponse(**data)


@router.post("", response_model=EnvironmentResponse, status_code=201)
async def create_environment(body: EnvironmentCreate, db: aiosqlite.Connection = Depends(get_db)):
    """Create a new environment and provision its sandbox."""
    env_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    config_json = json.dumps(body.config)

    # Provision the sandbox
    sandbox_info = await create_sandbox(body.sandbox_provider, body.config)

    await db.execute(
        "INSERT INTO environments (id, name, sandbox_provider, sandbox_id, sandbox_url, config, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (env_id, body.name, body.sandbox_provider, sandbox_info["sandbox_id"], sandbox_info["url"], config_json, now, now),
    )
    await db.commit()
    return EnvironmentResponse(
        id=env_id,
        name=body.name,
        sandbox_provider=body.sandbox_provider,
        sandbox_id=sandbox_info["sandbox_id"],
        sandbox_url=sandbox_info["url"],
        config=body.config,
        created_at=now,
        updated_at=now,
    )


@router.get("", response_model=list[EnvironmentResponse])
async def list_environments(db: aiosqlite.Connection = Depends(get_db)):
    """List all environments, ordered by most recently created first."""
    cursor = await db.execute("SELECT * FROM environments ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [_row_to_response(row) for row in rows]


@router.get("/{environment_id}", response_model=EnvironmentResponse)
async def get_environment(environment_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Get an environment by ID. Returns 404 if not found."""
    cursor = await db.execute("SELECT * FROM environments WHERE id = ?", (environment_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Environment not found")
    return _row_to_response(row)


@router.delete("/{environment_id}", status_code=204)
async def delete_environment(environment_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """Delete an environment and tear down its sandbox. Returns 404 if not found."""
    cursor = await db.execute(
        "SELECT sandbox_provider, sandbox_id FROM environments WHERE id = ?",
        (environment_id,),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Tear down the sandbox if it was provisioned
    env_data = dict(row)
    if env_data["sandbox_id"]:
        await destroy_sandbox(env_data["sandbox_provider"], env_data["sandbox_id"])

    await db.execute("DELETE FROM environments WHERE id = ?", (environment_id,))
    await db.commit()
