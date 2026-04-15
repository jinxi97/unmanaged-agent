import { describe, it, expect, beforeEach, vi } from "vitest";
import { UnmanagedAgentClient } from "../src/client";

const NOW = new Date().toISOString();

const AGENT_JSON = {
  id: "agent-1",
  name: "test-agent",
  model: "claude-sonnet-4-6",
  runtime: "pi-agent",
  system_prompt: "You are helpful.",
  created_at: NOW,
  updated_at: NOW,
};

const ENV_JSON = {
  id: "env-1",
  name: "test-env",
  sandbox_provider: "e2b",
  sandbox_id: "sandbox-123",
  sandbox_url: "https://sandbox-123.e2b.dev",
  config: { packages: ["python3"] },
  created_at: NOW,
  updated_at: NOW,
};

const SESSION_JSON = {
  id: "session-1",
  agent_id: "agent-1",
  environment_id: "env-1",
  title: "Test session",
  created_at: NOW,
  updated_at: NOW,
};

const EVENT_JSON = {
  id: "event-1",
  session_id: "session-1",
  type: "message",
  content: { text: "Hello!" },
  created_at: NOW,
};

let client: UnmanagedAgentClient;

beforeEach(() => {
  client = new UnmanagedAgentClient("http://test");
  vi.restoreAllMocks();
});

function mockFetch(body: unknown, status = 200) {
  vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as Response);
}

function mockFetchNoContent() {
  vi.spyOn(globalThis, "fetch").mockResolvedValue({
    ok: true,
    status: 204,
    json: async () => undefined,
    text: async () => "",
  } as Response);
}

// --- Agents ---

describe("agents", () => {
  it("create", async () => {
    mockFetch(AGENT_JSON, 201);
    const agent = await client.agents.create({
      name: "test-agent",
      model: "claude-sonnet-4-6",
    });
    expect(agent.id).toBe("agent-1");
    expect(agent.name).toBe("test-agent");
  });

  it("list", async () => {
    mockFetch([AGENT_JSON]);
    const agents = await client.agents.list();
    expect(agents).toHaveLength(1);
    expect(agents[0].id).toBe("agent-1");
  });

  it("get", async () => {
    mockFetch(AGENT_JSON);
    const agent = await client.agents.get("agent-1");
    expect(agent.id).toBe("agent-1");
  });

  it("delete", async () => {
    mockFetchNoContent();
    await client.agents.delete("agent-1");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "http://test/agents/agent-1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});

// --- Environments ---

describe("environments", () => {
  it("create", async () => {
    mockFetch(ENV_JSON, 201);
    const env = await client.environments.create({
      name: "test-env",
      sandbox_provider: "e2b",
    });
    expect(env.sandbox_id).toBe("sandbox-123");
  });

  it("list", async () => {
    mockFetch([ENV_JSON]);
    const envs = await client.environments.list();
    expect(envs).toHaveLength(1);
  });

  it("get", async () => {
    mockFetch(ENV_JSON);
    const env = await client.environments.get("env-1");
    expect(env.name).toBe("test-env");
  });

  it("delete", async () => {
    mockFetchNoContent();
    await client.environments.delete("env-1");
  });
});

// --- Sessions ---

describe("sessions", () => {
  it("create", async () => {
    mockFetch(SESSION_JSON, 201);
    const session = await client.sessions.create({
      agent_id: "agent-1",
      environment_id: "env-1",
      title: "Test session",
    });
    expect(session.agent_id).toBe("agent-1");
  });

  it("list", async () => {
    mockFetch([SESSION_JSON]);
    const sessions = await client.sessions.list();
    expect(sessions).toHaveLength(1);
  });

  it("get", async () => {
    mockFetch(SESSION_JSON);
    const session = await client.sessions.get("session-1");
    expect(session.title).toBe("Test session");
  });

  it("delete", async () => {
    mockFetchNoContent();
    await client.sessions.delete("session-1");
  });

  it("listEvents", async () => {
    mockFetch([EVENT_JSON]);
    const events = await client.sessions.listEvents("session-1");
    expect(events).toHaveLength(1);
    expect(events[0].type).toBe("message");
    expect(events[0].content).toEqual({ text: "Hello!" });
  });
});
