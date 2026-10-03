import type {
  CreateSessionInput,
  ProviderStatus,
  SeedDetail,
  SessionSummary,
  SessionView,
  TurnResult,
} from "@/lib/types";

function localApiBase(raw?: string): string {
  if (!raw) {
    if (
      typeof window !== "undefined" &&
      window.location.port === "3000"
    ) {
      return "http://127.0.0.1:8765/api/v1";
    }
    return "/api/v1";
  }

  const url = new URL(raw);
  if (
    !["http:", "https:"].includes(url.protocol) ||
    !["127.0.0.1", "localhost"].includes(url.hostname)
  ) {
    throw new Error(
      "Shadowseed web API must use a loopback URL (127.0.0.1 or localhost)",
    );
  }
  return raw.replace(/\/$/, "");
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(
    localApiBase(process.env.NEXT_PUBLIC_SHADOWSEED_API_URL) + path,
    {
      ...init,
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    },
  );

  const payload = (await response.json()) as T & { error?: string };
  if (!response.ok) {
    throw new Error(payload.error ?? "Request failed (" + response.status + ")");
  }
  return payload;
}

export async function getProviderStatus(): Promise<ProviderStatus[]> {
  const payload = await request<{ providers: ProviderStatus[] }>("/providers");
  return payload.providers;
}

export async function configureOpenAI(
  apiKey: string,
): Promise<ProviderStatus[]> {
  const payload = await request<{ providers: ProviderStatus[] }>(
    "/providers/openai/credential",
    {
      method: "POST",
      body: JSON.stringify({ api_key: apiKey }),
    },
  );
  return payload.providers;
}

export async function clearOpenAI(): Promise<ProviderStatus[]> {
  const payload = await request<{ providers: ProviderStatus[] }>(
    "/providers/openai/credential/clear",
    {
      method: "POST",
      body: "{}",
    },
  );
  return payload.providers;
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
  requestId: string,
  externalConfirmed = false,
): Promise<TurnResult> {
  return request<TurnResult>(
    "/sessions/" + encodeURIComponent(sessionId) + "/turns",
    {
      method: "POST",
      body: JSON.stringify({
        question,
        request_id: requestId,
        external_confirmed: externalConfirmed,
      }),
    },
  );
}


export async function getSeed(
  sessionId: string,
  seedId: string,
): Promise<SeedDetail> {
  return request<SeedDetail>(
    "/sessions/" +
      encodeURIComponent(sessionId) +
      "/seeds/" +
      encodeURIComponent(seedId),
  );
}

export async function submitSeedEvidence(
  sessionId: string,
  seedId: string,
  input: {
    sourceRef: string;
    note: string;
    requestId: string;
  },
): Promise<SessionView> {
  return request<SessionView>(
    "/sessions/" +
      encodeURIComponent(sessionId) +
      "/seeds/" +
      encodeURIComponent(seedId) +
      "/evidence",
    {
      method: "POST",
      body: JSON.stringify({
        source_ref: input.sourceRef,
        note: input.note,
        operator_verified: true,
        request_id: input.requestId,
      }),
    },
  );
}

export async function contradictSeed(
  sessionId: string,
  seedId: string,
  requestId: string,
): Promise<SessionView> {
  return request<SessionView>(
    "/sessions/" +
      encodeURIComponent(sessionId) +
      "/seeds/" +
      encodeURIComponent(seedId) +
      "/contradictions",
    {
      method: "POST",
      body: JSON.stringify({ request_id: requestId }),
    },
  );
}

export async function resolveSeedContradiction(
  sessionId: string,
  seedId: string,
  input: {
    basis: string;
    requestId: string;
  },
): Promise<SessionView> {
  return request<SessionView>(
    "/sessions/" +
      encodeURIComponent(sessionId) +
      "/seeds/" +
      encodeURIComponent(seedId) +
      "/contradictions/resolve",
    {
      method: "POST",
      body: JSON.stringify({
        basis: input.basis,
        request_id: input.requestId,
      }),
    },
  );
}
