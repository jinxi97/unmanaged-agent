"""Unmanaged Agent API Server."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from database import init_db
from routers import agents, environments, sessions

load_dotenv(override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Unmanaged Agent API",
    description="Open sourced agent infra. Create agents, environments, and sessions to run AI agents in sandboxed containers.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(agents.router)
app.include_router(environments.router)
app.include_router(sessions.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
