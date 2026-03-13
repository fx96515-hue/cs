"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import CommandPalette from "./CommandPalette";
import { ToastProvider } from "./ToastProvider";
import { DEMO_TOKEN } from "../../lib/api";

function hasToken(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(localStorage.getItem("token"));
}

function isDemoToken(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem("token") === DEMO_TOKEN;
}

/* ------------------------------------------------------------------ */
/*  Demo-Modus-Banner                                                   */
/* ------------------------------------------------------------------ */

function DemoModeBanner() {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "var(--space-3)",
      padding: "10px var(--space-5)",
      background: "var(--color-warning-subtle)",
      borderBottom: "1px solid var(--color-warning-border)",
      fontSize: "var(--font-size-sm)",
      color: "var(--color-warning)",
    }}>
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <span>
        <strong>Demo-Modus aktiv</strong> — Es werden keine echten Daten geladen.
        Starte das Backend und melde dich mit echten Zugangsdaten an.
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Offline-Banner                                                      */
/* ------------------------------------------------------------------ */

function OfflineBanner() {
  return (
    <div className="offlineBanner">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
        <line x1="1" y1="1" x2="23" y2="23"/>
        <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
        <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
        <path d="M10.71 5.05A16 16 0 0 1 22.56 9"/>
        <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
        <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
        <line x1="12" y1="20" x2="12.01" y2="20"/>
      </svg>
      <span>Keine Verbindung — Überprüfe deine Internetverbindung.</span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  AppShell                                                            */
/* ------------------------------------------------------------------ */

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [authed, setAuthed] = React.useState(false);
  const [isDemo, setIsDemo] = React.useState(false);
  const [offline, setOffline] = React.useState(false);
  const [cmdOpen, setCmdOpen] = React.useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);

  React.useEffect(() => {
    setAuthed(hasToken());
    setIsDemo(isDemoToken());
  }, [pathname]);

  // Online/Offline erkennen
  React.useEffect(() => {
    const goOffline = () => setOffline(true);
    const goOnline = () => setOffline(false);
    window.addEventListener("offline", goOffline);
    window.addEventListener("online", goOnline);
    return () => {
      window.removeEventListener("offline", goOffline);
      window.removeEventListener("online", goOnline);
    };
  }, []);

  // ⌘K / Ctrl+K öffnen
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCmdOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Login-Seite ohne Chrome
  if (pathname === "/login") {
    return (
      <ToastProvider>
        {children}
      </ToastProvider>
    );
  }

  return (
    <ToastProvider>
      <div className="shell">
        <Sidebar
          authed={authed}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
        />
        <div className="main">
          <Topbar
            authed={authed}
            onLogout={() => {
              localStorage.removeItem("token");
              setAuthed(false);
              router.push("/login");
            }}
            onOpenCmd={() => setCmdOpen(true)}
          />
          {offline && <OfflineBanner />}
          {isDemo && !offline && <DemoModeBanner />}
          <main className="page">{children}</main>
        </div>
      </div>
      {/* Command-Palette global – hat eigenen ⌘K listener, kann aber auch von außen gesteuert werden */}
      <CommandPalette forceOpen={cmdOpen} onForceClose={() => setCmdOpen(false)} />
    </ToastProvider>
  );
}
