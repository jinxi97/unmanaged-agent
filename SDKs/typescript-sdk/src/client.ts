/** Unmanaged Agent API client. */

import type {
  Agent,
  AgentCreateParams,
  Environment,
  EnvironmentCreateParams,
  Event,
  EventCreateParams,
  Session,
  SessionCreateParams,
  SSEEvent,
} from "./types";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  baseUrl: string,
  method: string,
  path: string,
  body?: unknown,
  timeout?: number,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout ?? 30_000);

  try {
    const res = await fetch(`${baseUrl}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new ApiError(res.status, text);
    }

    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

// --- Resource classes ---

export class AgentsResource {
  constructor(private baseUrl: string) {}

  /** Create a new agent. */
  async create(params: AgentCreateParams): Promise<Agent> {
    return request<Agent>(this.baseUrl, "POST", "/agents", {
      name: params.name,
      model: params.model,
      runtime: params.runtime ?? "pi-agent",
      system_prompt: params.system_prompt ?? "",
    });
  }

  /** List all agents. */
  async list(): Promise<Agent[]> {
    return request<Agent[]>(this.baseUrl, "GET", "/agents");
  }

  /** Get an agent by ID. */
  async get(agentId: string): Promise<Agent> {
    return request<Agent>(this.baseUrl, "GET", `/agents/${agentId}`);
  }

  /** Delete an agent by ID. */
  async delete(agentId: string): Promise<void> {
    return request<void>(this.baseUrl, "DELETE", `/agents/${agentId}`);
  }
}

export class EnvironmentsResource {
  constructor(private baseUrl: string) {}

  /** Create a new environment and provision its sandbox. */
  async create(params: EnvironmentCreateParams): Promise<Environment> {
    return request<Environment>(
      this.baseUrl,
      "POST",
      "/environments",
      {
        name: params.name,
        sandbox_provider: params.sandbox_provider,
        config: params.config ?? {},
      },
      300_000,
    );
  }

  /** List all environments. */
  async list(): Promise<Environment[]> {
    return request<Environment[]>(this.baseUrl, "GET", "/environments");
  }

  /** Get an environment by ID. */
  async get(environmentId: string): Promise<Environment> {
    return request<Environment>(
      this.baseUrl,
      "GET",
      `/environments/${environmentId}`,
    );
  }

  /** Delete an environment and tear down its sandbox. */
  async delete(environmentId: string): Promise<void> {
    return request<void>(
      this.baseUrl,
      "DELETE",
      `/environments/${environmentId}`,
    );
  }
}

export class SessionsResource {
  constructor(private baseUrl: string) {}

  /** Create a new session. */
  async create(params: SessionCreateParams): Promise<Session> {
    return request<Session>(this.baseUrl, "POST", "/sessions", {
      agent_id: params.agent_id,
      environment_id: params.environment_id,
      title: params.title ?? "",
    });
  }

  /** List all sessions. */
  async list(): Promise<Session[]> {
    return request<Session[]>(this.baseUrl, "GET", "/sessions");
  }

  /** Get a session by ID. */
  async get(sessionId: string): Promise<Session> {
    return request<Session>(this.baseUrl, "GET", `/sessions/${sessionId}`);
  }

  /** Delete a session. */
  async delete(sessionId: string): Promise<void> {
    return request<void>(this.baseUrl, "DELETE", `/sessions/${sessionId}`);
  }

  /**
   * Send an event and stream back SSE responses.
   * Yields parsed SSE events as they arrive.
   */
  async *sendEvent(
    sessionId: string,
    params: EventCreateParams,
  ): AsyncGenerator<SSEEvent> {
    const res = await fetch(
      `${this.baseUrl}/sessions/${sessionId}/events`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: params.type ?? "message",
          content: params.content,
        }),
      },
    );

    if (!res.ok) {
      const text = await res.text();
      throw new ApiError(res.status, text);
    }

    if (!res.body) return;

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let eventType: string | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7);
        } else if (line.startsWith("data: ")) {
          const raw = line.slice(6);
          let data: unknown;
          try {
            data = JSON.parse(raw);
          } catch {
            data = raw;
          }
          yield { event: eventType, data };
          eventType = null;
        }
      }
    }
  }

  /** Fetch the full event history for a session. */
  async listEvents(sessionId: string): Promise<Event[]> {
    return request<Event[]>(
      this.baseUrl,
      "GET",
      `/sessions/${sessionId}/events`,
    );
  }
}

// --- Main client ---

export class UnmanagedAgentClient {
  public agents: AgentsResource;
  public environments: EnvironmentsResource;
  public sessions: SessionsResource;

  constructor(baseUrl: string = "http://localhost:8000") {
    this.agents = new AgentsResource(baseUrl);
    this.environments = new EnvironmentsResource(baseUrl);
    this.sessions = new SessionsResource(baseUrl);
  }
}
