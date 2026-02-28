"use client";

import { useState } from "react";
import { apiFetch, setToken, Token } from "../../lib/api";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  // Must be a valid email; avoid .local/.test (EmailStr rejects these).
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const t = await apiFetch<Token>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(t.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    }
  }

  return (
    <div className="authRoot">
      <div className="authShell">
        <section className="authHero">
          <div className="authBrand">
            <div className="authBadge">CS</div>
            <div>
              <div className="authBrandTitle">CoffeeStudio</div>
              <div className="authBrandSub">Intelligence Platform</div>
            </div>
          </div>
          <h1 className="authTitle">Sourcing. Risk. Signal.</h1>
          <p className="authLead">
            Secure access to market intelligence, supplier quality, and
            operational workflows. Built for fast, auditable decisions.
          </p>
          <div className="authHighlights">
            <div className="authHighlight">
              <div className="authHighlightValue">384</div>
              <div className="authHighlightLabel">Embedding dims</div>
            </div>
            <div className="authHighlight">
              <div className="authHighlightValue">17</div>
              <div className="authHighlightLabel">Demo coops</div>
            </div>
            <div className="authHighlight">
              <div className="authHighlightValue">8</div>
              <div className="authHighlightLabel">Roasters</div>
            </div>
          </div>
          <div className="authNote">
            First run: call <code>POST /auth/dev/bootstrap</code> in the backend.
          </div>
        </section>

        <section className="authPanel">
          <div className="authPanelHeader">
            <div className="authPanelTitle">Sign in</div>
            <div className="authPanelSub">Use your admin credentials</div>
          </div>

          <form onSubmit={onSubmit} className="authForm">
            <label className="field">
              <span className="fieldLabel">Email</span>
              <input
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@coffeestudio.com"
                autoComplete="email"
              />
            </label>
            <label className="field">
              <span className="fieldLabel">Password</span>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your secure password"
                autoComplete="current-password"
              />
            </label>
            <button type="submit" className="btn btnPrimary btnFull">
              Access dashboard
            </button>
            {error && <div className="authError">{error}</div>}
          </form>

          <div className="authFooter">
            <div className="authFootItem">End-to-end audit trail</div>
            <div className="authFootItem">Real-time price signals</div>
            <div className="authFootItem">ML scoring workflows</div>
          </div>
        </section>
      </div>
    </div>
  );
}
