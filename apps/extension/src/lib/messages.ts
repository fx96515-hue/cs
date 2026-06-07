// Typed message protocol between the popup and the background service worker.
// The popup never talks to the network directly — it asks the worker, which
// holds the token and owns host_permissions (so requests bypass page CORS).
import type {
  AssistantAnswer,
  AssistantStatus,
  AuthStatus,
  CooperativeDraft,
  EntityCreated,
  ExtractedPage,
  RoasterDraft,
} from "./types";

export type Request =
  | { type: "auth.status" }
  | { type: "auth.login"; email: string; password: string }
  | { type: "auth.logout" }
  | { type: "config.setBaseUrl"; baseUrl: string }
  | { type: "page.extract" }
  | { type: "entity.create"; entityType: "roaster"; draft: RoasterDraft }
  | { type: "entity.create"; entityType: "cooperative"; draft: CooperativeDraft }
  | { type: "assistant.status" }
  | { type: "assistant.ask"; message: string; sessionId?: string };

export type Response<T> = { ok: true; data: T } | { ok: false; error: string };

export interface ResultMap {
  "auth.status": AuthStatus;
  "auth.login": AuthStatus;
  "auth.logout": { done: true };
  "config.setBaseUrl": AuthStatus;
  "page.extract": ExtractedPage;
  "entity.create": EntityCreated;
  "assistant.status": AssistantStatus;
  "assistant.ask": AssistantAnswer;
}

/** Promise-based wrapper around chrome.runtime.sendMessage with typed results. */
export async function send<K extends Request["type"]>(
  message: Extract<Request, { type: K }>,
): Promise<ResultMap[K]> {
  const res = (await chrome.runtime.sendMessage(message)) as Response<ResultMap[K]>;
  if (!res || !res.ok) {
    throw new Error(res?.error ?? "No response from background worker");
  }
  return res.data;
}
