/** Data models for the Unmanaged Agent API. */

export interface Agent {
  id: string;
  name: string;
  model: string;
  runtime: string;
  system_prompt: string;
  created_at: string;
  updated_at: string;
}

export interface AgentCreateParams {
  name: string;
  model: string;
  runtime?: string;
  system_prompt?: string;
}

export interface Environment {
  id: string;
  name: string;
  sandbox_provider: string;
  sandbox_id: string | null;
  sandbox_url: string | null;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EnvironmentCreateParams {
  name: string;
  sandbox_provider: string;
  config?: Record<string, unknown>;
}

export interface Session {
  id: string;
  agent_id: string;
  environment_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface SessionCreateParams {
  agent_id: string;
  environment_id: string;
  title?: string;
}

export interface Event {
  id: string;
  session_id: string;
  type: string;
  content: Record<string, unknown>;
  created_at: string;
}

export interface EventCreateParams {
  type?: string;
  content: Record<string, unknown>;
}

export interface SSEEvent {
  event: string | null;
  data: unknown;
}
