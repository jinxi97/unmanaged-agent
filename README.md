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

## Roadmap

- [ ] **Metadata storage**: Currently using SQLite. PostgreSQL/Neon DB support is on the way.
- [ ] **SDKs**: Python and TypeScript client SDKs.
