// Thin client for the CoffeeStudio API. Runs inside the background service
// worker, which has host_permissions for the API origin.
import type {
  AssistantAnswer,
  AssistantStatus,
  CooperativeDraft,
  EntityCreated,
  RoasterDraft,
  UserOut,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

async function request<T>(
  baseUrl: string,
  path: string,
  init: RequestInit & { token?: string } = {},
): Promise<T> {
  const { token, headers, ...rest } = init;
  const res = await fetch(`${baseUrl}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!res.ok) {
    throw new ApiError(await extractError(res), res.status);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

/** FastAPI/Pydantic errors put a string or a list of issues in `detail`. */
async function extractError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((d) => (d as { msg?: string }).msg ?? JSON.stringify(d))
        .join("; ");
    }
  } catch {
    /* fall through to status text */
  }
  return `${res.status} ${res.statusText}`;
}

export async function login(
  baseUrl: string,
  email: string,
  password: string,
): Promise<string> {
  const body = await request<TokenResponse>(baseUrl, "/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return body.access_token;
}

export function fetchMe(baseUrl: string, token: string): Promise<UserOut> {
  return request<UserOut>(baseUrl, "/auth/me", { token });
}

export function createRoaster(
  baseUrl: string,
  token: string,
  draft: RoasterDraft,
): Promise<EntityCreated> {
  return request<EntityCreated>(baseUrl, "/roasters/", {
    method: "POST",
    token,
    body: JSON.stringify(draft),
  });
}

export function createCooperative(
  baseUrl: string,
  token: string,
  draft: CooperativeDraft,
): Promise<EntityCreated> {
  return request<EntityCreated>(baseUrl, "/cooperatives/", {
    method: "POST",
    token,
    body: JSON.stringify(draft),
  });
}

export function assistantStatus(baseUrl: string, token: string): Promise<AssistantStatus> {
  return request<AssistantStatus>(baseUrl, "/assistant/status", { token });
}

interface ChatEvent {
  type: "session" | "chunk" | "done" | "error";
  session_id?: string;
  content?: string;
  sources?: unknown[];
  message?: string;
}

/**
 * Calls the SSE chat endpoint and accumulates the streamed token chunks into a
 * single answer. (A live token stream would need a long-lived port; this v1
 * keeps the message protocol request/response.)
 */
export async function assistantChat(
  baseUrl: string,
  token: string,
  message: string,
  sessionId?: string,
): Promise<AssistantAnswer> {
  const res = await fetch(`${baseUrl}/assistant/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!res.ok) throw new ApiError(await extractError(res), res.status);
  if (!res.body) throw new ApiError("No response stream", 502);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  const answer: AssistantAnswer = { text: "", sources: [], sessionId };
  let buffer = "";

  const consume = (block: string): void => {
    for (const line of block.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const payload = trimmed.slice(5).trim();
      if (!payload || payload === "[DONE]") continue;
      let evt: ChatEvent;
      try {
        evt = JSON.parse(payload) as ChatEvent;
      } catch {
        continue;
      }
      if (evt.type === "session" && evt.session_id) answer.sessionId = evt.session_id;
      else if (evt.type === "chunk" && evt.content) answer.text += evt.content;
      else if (evt.type === "done")
        answer.sources = (evt.sources ?? []).map((s) => String(s));
      else if (evt.type === "error") throw new ApiError(evt.message ?? "Assistant error", 502);
    }
  };

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      consume(buffer.slice(0, sep));
      buffer = buffer.slice(sep + 2);
    }
  }
  if (buffer.trim()) consume(buffer);
  return answer;
}
