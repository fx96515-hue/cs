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
    <div>
      <h1>Anmeldung</h1>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 8, maxWidth: 360 }}>
        <label>
          E-Mail
          <input value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%" }} />
        </label>
        <label>
          Passwort
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: "100%" }} />
        </label>
        <button type="submit">Anmelden</button>
        {error && <div style={{ color: "crimson" }}>{error}</div>}
      </form>
      <p style={{ opacity: 0.7 }}>
        Hinweis: Beim ersten Start bitte im Backend einmal <code>POST /auth/dev/bootstrap</code> ausführen.
      </p>
    </div>
  );
}
