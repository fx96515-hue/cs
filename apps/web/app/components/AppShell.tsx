"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { DEMO_TOKEN } from "../../lib/api";

function hasToken(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(localStorage.getItem("token"));
}

function isDemoToken(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem("token") === DEMO_TOKEN;
}

function DemoModeBanner() {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "var(--space-3)",
      padding: "10px var(--space-5)",
      background: "var(--color-warn-subtle)",
      borderBottom: "1px solid var(--color-warn)",
      fontSize: "var(--font-size-sm)",
      color: "var(--color-warn-fg)",
    }}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <span>
        <strong>Demo-Modus:</strong> Es werden keine echten Daten geladen. Starte das Backend und melde dich mit echten Zugangsdaten an.
      </span>
    </div>
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = React.useState(false);
  const [isDemo, setIsDemo] = React.useState(false);

  React.useEffect(() => {
    setAuthed(hasToken());
    setIsDemo(isDemoToken());
  }, [pathname]);

  // Login-Seite ohne Chrome anzeigen
  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <div className="shell">
      <Sidebar authed={authed} />
      <div className="main">
        <Topbar
          authed={authed}
          onLogout={() => {
            localStorage.removeItem("token");
            setAuthed(false);
            router.push("/login");
          }}
        />
        {isDemo && <DemoModeBanner />}
        <main className="page">{children}</main>
      </div>
    </div>
  );
}
