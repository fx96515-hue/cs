// Thin client for the CoffeeStudio API. Runs inside the background service
// worker, which has host_permissions for the API origin.
import type { RoasterCreated, RoasterDraft, UserOut } from "./types";

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
): Promise<RoasterCreated> {
  return request<RoasterCreated>(baseUrl, "/roasters/", {
    method: "POST",
    token,
    body: JSON.stringify(draft),
  });
}
