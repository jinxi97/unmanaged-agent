# Unmanaged Agent TypeScript SDK

TypeScript client for the [Unmanaged Agent API](../../api-server/).

## Install

```bash
npm install unmanaged-agent
```

## Usage

```typescript
import { UnmanagedAgentClient } from "unmanaged-agent";

const client = new UnmanagedAgentClient("http://localhost:8000");

// Create an agent
const agent = await client.agents.create({
  name: "coding-assistant",
  model: "claude-sonnet-4-6",
  system_prompt: "You are a helpful coding assistant.",
});

// Create an environment
const env = await client.environments.create({
  name: "python-sandbox",
  sandbox_provider: "e2b",
  config: { packages: ["python3"] },
});

// Create a session
const session = await client.sessions.create({
  agent_id: agent.id,
  environment_id: env.id,
  title: "My first session",
});

// Send a message and stream the response
for await (const event of client.sessions.sendEvent(session.id, {
  type: "message",
  content: { text: "Write a hello world script in Python." },
})) {
  console.log(event.event, event.data);
}

// Fetch event history
const events = await client.sessions.listEvents(session.id);
```
