import type {
  CreateSessionInput,
  SessionSummary,
  SessionView,
  TurnResult,
} from "@/lib/types";

const API_BASE =
  process.env.NEXT_PUBLIC_SHADOWSEED_API_URL ??
  "http://127.0.0.1:8765/api/v1";

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(API_BASE + path, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  const payload = (await response.json()) as T & { error?: string };
  if (!response.ok) {
    throw new Error(payload.error ?? "Request failed (" + response.status + ")");
  }
  return payload;
}

export async function listSessions(): Promise<SessionSummary[]> {
  const payload = await request<{ sessions: SessionSummary[] }>("/sessions");
  return payload.sessions;
}

export async function getSession(sessionId: string): Promise<SessionView> {
  return request<SessionView>("/sessions/" + encodeURIComponent(sessionId));
}

export async function createSession(
  input: CreateSessionInput,
): Promise<SessionView> {
  return request<SessionView>("/sessions", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function sendTurn(
  sessionId: string,
  question: string,
): Promise<TurnResult> {
  return request<TurnResult>(
    "/sessions/" + encodeURIComponent(sessionId) + "/turns",
    {
      method: "POST",
      body: JSON.stringify({ question }),
    },
  );
}
