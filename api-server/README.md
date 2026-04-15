# API Server

FastAPI server with SQLite persistence. Manages agents, environments, and sessions for running AI agents in sandboxed containers.

## Quick Start

```bash
# Install dependencies
uv sync

# Run the server
uv run uvicorn main:app --reload

# Open API docs
open http://localhost:8000/docs
```

### Docker

```bash
docker build -t unmanaged-agent .
docker run -p 8000:8000 unmanaged-agent
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `E2B_API_KEY` | API key for E2B sandbox |
| `DAYTONA_API_KEY` | API key for Daytona sandbox |

Create a `.env` file in the `api-server/` directory to set these.

## Endpoints

### Agent

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agents` | Create an agent |
| `GET` | `/agents` | List agents |
| `GET` | `/agents/{agent_id}` | Get an agent |
| `DELETE` | `/agents/{agent_id}` | Delete an agent |

### Environment

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/environments` | Create an environment |
| `GET` | `/environments` | List environments |
| `GET` | `/environments/{environment_id}` | Get an environment |
| `DELETE` | `/environments/{environment_id}` | Delete an environment |

### Session

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/sessions` | Create a session |
| `GET` | `/sessions` | List sessions |
| `GET` | `/sessions/{session_id}` | Get a session |
| `DELETE` | `/sessions/{session_id}` | Delete a session |
| `POST` | `/sessions/{session_id}/events` | Send an event (SSE streaming response) |
| `GET` | `/sessions/{session_id}/events` | Get event history for a session |

## Example Usage

### 1. Create an Agent

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-agent",
    "model": "claude-sonnet-4-6",
    "runtime": "pi-agent",
    "system_prompt": "You are a helpful coding assistant."
  }'
```

### 2. Create an Environment

```bash
curl -X POST http://localhost:8000/environments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "python-sandbox",
    "sandbox_provider": "e2b",
    "config": {
      "packages": ["python3", "nodejs"],
      "network": {"outbound": true}
    }
  }'
```

### 3. Create a Session

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "<agent_id>",
    "environment_id": "<environment_id>",
    "title": "Debug my script"
  }'
```

### 4. Send an Event (SSE Streaming)

```bash
curl -N -X POST http://localhost:8000/sessions/<session_id>/events \
  -H "Content-Type: application/json" \
  -d '{
    "type": "message",
    "content": {"text": "Hello, agent!"}
  }'
```

### 5. Fetch Event History

```bash
curl http://localhost:8000/sessions/<session_id>/events
```
