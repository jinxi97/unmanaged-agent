# Unmanaged Agent

Open sourced agent infra.

## How It Works

### 1. Create an Agent

Define the model, system prompt, tools, MCP servers, and skills. Create the agent once and reference it by ID across sessions.

> For the first version, only [pi-agent](https://github.com/badlogic/pi-mono/) is supported as the agent runtime. Support for [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk), [OpenAI Agents SDK](https://github.com/openai/openai-agents-python), and [Google ADK](https://github.com/google/adk-python) is coming soon.

### 2. Create an Environment

Configure a cloud container with pre-installed packages (Python, Node.js, Go, etc.), network access rules, and mounted files.

> Sandbox provided by [E2B](https://e2b.dev) and [Daytona](https://daytona.io). Support for [Blaxel](https://blaxel.ai) and [Modal](https://modal.com) is coming soon.

### 3. Start a Session

Launch a session that references your agent and environment configuration.

### 4. Send Events and Stream Responses

Send user messages as events. The agent autonomously executes tools and streams back results via server-sent events (SSE). Event history is persisted server-side and can be fetched in full.

## Quick Start

### 1. Create an agent

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "coding-assistant",
    "model": "claude-sonnet-4-6",
    "runtime": "pi-agent",
    "system_prompt": "You are a helpful coding assistant."
  }'
```

### 2. Create an environment

```bash
curl -X POST http://localhost:8000/environments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "python-sandbox",
    "sandbox_provider": "e2b",
    "config": {"packages": ["python3", "nodejs"]}
  }'
```

### 3. Create a session

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "<agent_id>",
    "environment_id": "<environment_id>",
    "title": "My first session"
  }'
```

### 4. Send a message and stream the response

```bash
curl -N -X POST http://localhost:8000/sessions/<session_id>/events \
  -H "Content-Type: application/json" \
  -d '{"type": "message", "content": {"text": "Write a Python script that prints the first 10 Fibonacci numbers."}}'
```

## Self-Hosting Guide

### Prerequisites

- Python 3.14+
- An [E2B](https://e2b.dev) API key (for sandbox environments)
- At least one LLM API key (Anthropic, OpenAI, Gemini, or OpenRouter)

### Option 1: Run directly

```bash
cd api-server

# Copy and fill in your API keys
cp .env.example .env

# Install dependencies
uv sync

# Start the server
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Option 2: Docker

```bash
cd api-server

docker build -t unmanaged-agent .

docker run -p 8000:8000 \
  -e E2B_API_KEY=your_e2b_key \
  -e ANTHROPIC_API_KEY=your_anthropic_key \
  unmanaged-agent
```

The API docs are available at `http://localhost:8000/docs`.

## Roadmap

- [ ] **Metadata storage**: Currently using SQLite. PostgreSQL/Neon DB support is on the way.
- [ ] **SDKs**: Python and TypeScript client SDKs.
