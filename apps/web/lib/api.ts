export type Token = {
  access_token: string;
  token_type?: string;
  expires_in?: number;
};

/**
 * Strukturierter API-Fehler mit HTTP-Statuscode und optionalem Fehlercode vom Backend.
 * Wird in allen apiFetch-Aufrufen geworfen. Erlaubt Komponenten gezielt auf
 * bestimmte Statuscodes zu reagieren (z.B. 401 für Session-Ablauf, 422 für Validierung).
 */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly code?: string,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isUnauthorized() { return this.status === 401; }
  get isForbidden()    { return this.status === 403; }
  get isNotFound()     { return this.status === 404; }
  get isValidation()   { return this.status === 422; }
  get isServerError()  { return this.status >= 500; }
}

type ApiFetchOptions = RequestInit & {
  /** If true, do not attach Authorization header */
  skipAuth?: boolean;
  /** If true, do not attempt token refresh on 401 */
  _isRetry?: boolean;
};

const TOKEN_KEY = "token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  const v = window.localStorage.getItem(TOKEN_KEY);
  return v && v.trim() ? v : null;
}

export function setToken(token?: string | null) {
  if (typeof window === "undefined") return;
  const t = (token || "").trim();
  if (!t) {
    window.localStorage.removeItem(TOKEN_KEY);
    return;
  }
  window.localStorage.setItem(TOKEN_KEY, t);
}

export function apiBaseUrl(): string {
  // Priority order:
  // 1. NEXT_PUBLIC_API_URL environment variable (set at build time in Next.js)
  //    - In docker-compose.yml, this is set to http://localhost:8000
  //    - This value is baked into the frontend bundle at build time
  // 2. If running server-side (SSR/SSG), use http://localhost:8000
  // 3. If browser is on Traefik hostname (ui.localhost), use Traefik API (api.localhost)
  // 4. Fallback to direct port access (http://localhost:8000)
  //
  // Note: The apiFetch function also has a fallback mechanism that will retry
  // with http://localhost:8000 if api.localhost fails, providing resilience
  // for local development scenarios.
  
  const env = process.env.NEXT_PUBLIC_API_URL;
  if (env) return env;

  if (typeof window === "undefined") return "http://localhost:8000";

  // If UI served via Traefik hostname, use Traefik API hostname too
  if (window.location.hostname === "ui.localhost") return "http://api.localhost";

  // Fallback (direct port)
  return "http://localhost:8000";
}

export const DEMO_TOKEN = "demo_token_for_preview";

export function isDemoMode(): boolean {
  return getToken() === DEMO_TOKEN;
}

export async function apiFetch<T = unknown>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { skipAuth, _isRetry, ...req } = options;

  const token = !skipAuth ? getToken() : null;

  const headers: Record<string, string> = {
    ...(req.headers as Record<string, string>),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  // auto JSON content-type when body is string and not set
  if (req.body && typeof req.body === "string" && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const base = apiBaseUrl();
  const url = `${base}${path}`;

  const tryFetch = async (u: string) => {
    const res = await fetch(u, { ...req, headers });
    if (!res.ok) {
      // Versuche strukturierten Fehler vom Backend zu lesen
      let errorBody: { detail?: string; code?: string; message?: string } = {};
      try { errorBody = await res.json(); } catch { /* kein JSON */ }

      const message =
        errorBody.detail || errorBody.message ||
        `API error: ${res.status}`;
      const code = errorBody.code;

      throw new ApiError(res.status, message, code, errorBody);
    }
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) return (await res.json()) as T;
    return (await res.text()) as unknown as T;
  };

  try {
    return await tryFetch(url);
  } catch (e) {
    // 401: Token abgelaufen → silent refresh versuchen
    if (
      e instanceof ApiError &&
      e.isUnauthorized &&
      !_isRetry &&
      !skipAuth &&
      token &&
      token !== DEMO_TOKEN
    ) {
      try {
        const refreshed = await apiFetch<Token>("/auth/refresh", {
          method: "POST",
          _isRetry: true,
        });
        setToken(refreshed.access_token);
        // Original-Request mit neuem Token wiederholen
        return apiFetch<T>(path, { ...options, _isRetry: true });
      } catch {
        // Refresh fehlgeschlagen → Token löschen und Fehler weitergeben
        setToken(null);
        throw e;
      }
    }

    // Fallback: Traefik-Host → direkter Backend-Port
    if (!(e instanceof ApiError) && base.includes("api.localhost")) {
      return await tryFetch(`http://localhost:8000${path}`);
    }
    throw e;
  }
}
