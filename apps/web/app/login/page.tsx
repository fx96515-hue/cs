"use client";

import { useState } from "react";
import { apiFetch, setToken, Token } from "../../lib/api";
import { useRouter } from "next/navigation";
import { toErrorMessage } from "../utils/error";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    // Demo mode - bypass API and set mock token
    if (demoMode) {
      setToken("demo_token_for_preview");
      router.push("/dashboard");
      return;
    }

    try {
      const t = await apiFetch<Token>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(t.access_token);
      router.push("/dashboard");
    } catch (error: unknown) {
      const msg = toErrorMessage(error) || "Login failed";
      if (msg.includes("fetch") || msg.includes("network")) {
        setError("API nicht erreichbar. Aktiviere den Demo-Modus oder starte das Backend.");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="authRoot">
      <div className="authShell">
        <section className="authPanel">
          <div className="authBrand">
            <div className="authBadge">CS</div>
            <div>
              <div className="authBrandTitle">CoffeeStudio</div>
              <div className="authBrandSub">Intelligence Platform</div>
            </div>
          </div>

          <div className="authPanelHeader">
            <div className="authPanelTitle">Willkommen</div>
            <div className="authPanelSub">Melde dich an, um fortzufahren</div>
          </div>

          <form onSubmit={onSubmit} className="authForm">
            <label className="field">
              <span className="fieldLabel">E-Mail</span>
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@coffeestudio.com"
                autoComplete="email"
                disabled={demoMode}
              />
            </label>
            <label className="field">
              <span className="fieldLabel">Passwort</span>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Dein Passwort"
                autoComplete="current-password"
                disabled={demoMode}
              />
            </label>

            <label className="demoCheckbox">
              <input
                type="checkbox"
                checked={demoMode}
                onChange={(e) => setDemoMode(e.target.checked)}
              />
              <div>
                <span>Demo-Modus</span>
                <small>Ohne Backend-Verbindung erkunden</small>
              </div>
            </label>

            {error && <div className="authError">{error}</div>}

            <button 
              type="submit" 
              className="btn btnPrimary btnFull"
              disabled={loading}
            >
              {loading ? "Wird geladen..." : demoMode ? "Demo starten" : "Anmelden"}
            </button>
          </form>

          <div className="authFooter">
            <div className="authFootItem">
              End-to-End Audit Trail
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
