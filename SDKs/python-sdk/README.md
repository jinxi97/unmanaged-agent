# Unmanaged Agent Python SDK

Python client for the [Unmanaged Agent API](../../api-server/).

## Install

```bash
pip install unmanaged-agent
```

## Usage

```python
from unmanaged_agent import UnmanagedAgentClient

client = UnmanagedAgentClient("http://localhost:8000")

# Create an agent
agent = client.agents.create(
    name="coding-assistant",
    model="claude-sonnet-4-6",
    system_prompt="You are a helpful coding assistant.",
)

# Create an environment
env = client.environments.create(
    name="python-sandbox",
    sandbox_provider="e2b",
    config={"packages": ["python3"]},
)

# Create a session
session = client.sessions.create(
    agent_id=agent.id,
    environment_id=env.id,
    title="My first session",
)

# Send a message and stream the response
for event in client.sessions.send_event(
    session.id,
    type="message",
    content={"text": "Write a hello world script in Python."},
):
    print(event["event"], event["data"])

# Fetch event history
events = client.sessions.list_events(session.id)
```

### Async

```python
import asyncio
from unmanaged_agent import AsyncUnmanagedAgentClient

async def main():
    async with AsyncUnmanagedAgentClient("http://localhost:8000") as client:
        agent = await client.agents.create(
            name="coding-assistant",
            model="claude-sonnet-4-6",
        )

        env = await client.environments.create(
            name="python-sandbox",
            sandbox_provider="e2b",
        )

        session = await client.sessions.create(
            agent_id=agent.id,
            environment_id=env.id,
        )

        async for event in client.sessions.send_event(
            session.id,
            type="message",
            content={"text": "Hello!"},
        ):
            print(event["event"], event["data"])

asyncio.run(main())
```
