/**
 * services/auth.service.ts
 * Authentifizierungs-Service: Login, Logout, Token-Refresh.
 */
import { apiFetch, setToken, getToken, DEMO_TOKEN, Token } from "../../lib/api";

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
    setToken(token.access_token);
    return token;
  },

  /**
   * Demo-Login ohne Backend.
   */
  loginDemo(): void {
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
    setToken(res.access_token);
    return res.access_token;
  },

  /**
   * Abmelden: Token lokal löschen.
   */
  logout(): void {
    setToken(null);
  },

  /**
   * Prüft ob ein (nicht-Demo) Token vorhanden ist.
   */
  isAuthenticated(): boolean {
    const t = getToken();
    return !!t && t !== DEMO_TOKEN;
  },
};
