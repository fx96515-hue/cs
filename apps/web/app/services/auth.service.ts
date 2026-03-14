/**
 * services/auth.service.ts
 * Authentifizierungs-Service: Login, Logout, Token-Refresh.
 */
import {
  apiFetch,
  clearAuthState,
  DEMO_TOKEN,
  getToken,
  hasAuthSession,
  logoutSession,
  setAuthSession,
  setToken,
  Token,
} from "../../lib/api";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RefreshResponse {
  access_token: string;
  expires_in?: number;
}

export const AuthService = {
  /**
   * Benutzer anmelden. Gibt Token zurück und speichert ihn.
   */
  async login(credentials: LoginCredentials): Promise<Token> {
    const token = await apiFetch<Token>("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
      skipAuth: true,
    });
    clearAuthState();
    setAuthSession(true);
    return token;
  },

  /**
   * Demo-Login ohne Backend.
   */
  loginDemo(): void {
    clearAuthState();
    setToken(DEMO_TOKEN);
  },

  /**
   * Token erneuern (silent refresh).
   * Gibt neuen Access-Token zurück oder wirft, wenn nicht möglich.
   */
  async refresh(): Promise<string> {
    const res = await apiFetch<RefreshResponse>("/auth/refresh", {
      method: "POST",
    });
    setAuthSession(true);
    return res.access_token;
  },

  /**
   * Abmelden: Token lokal löschen.
   */
  async logout(): Promise<void> {
    await logoutSession();
  },

  /**
   * Prüft ob ein (nicht-Demo) Token vorhanden ist.
   */
  isAuthenticated(): boolean {
    const t = getToken();
    return (hasAuthSession() || (!!t && t !== DEMO_TOKEN)) && t !== DEMO_TOKEN;
  },
};
