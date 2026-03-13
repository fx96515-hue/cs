"use client";

import { useRouter } from "next/navigation";
import React, { useCallback, useEffect, useRef, useState } from "react";

/* ------------------------------------------------------------------ */
/*  Alle navigierbaren Seiten                                           */
/* ------------------------------------------------------------------ */

interface CmdEntry {
  label: string;
  description: string;
  href: string;
  category: string;
  icon: React.ReactNode;
  shortcut?: string;
}

const SearchIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
  </svg>
);

const NavIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

const entries: CmdEntry[] = [
  // Übersicht
  { label: "Dashboard", description: "Systemstatus und Kennzahlen", href: "/dashboard", category: "Übersicht", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>, shortcut: "G D" },
  // Einkauf
  { label: "Kooperativen", description: "Lieferanten und Partner verwalten", href: "/cooperatives", category: "Einkauf", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>, shortcut: "G C" },
  { label: "Peru Einkauf", description: "Sourcing aus peruanischen Regionen", href: "/peru-sourcing", category: "Einkauf", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="10" r="3"/><path d="M12 2a8 8 0 0 0-8 8c0 5.4 7 12 8 12s8-6.6 8-12a8 8 0 0 0-8-8z"/></svg> },
  { label: "Kaffee-Partien", description: "Ernte-Partien und Chargen", href: "/lots", category: "Einkauf", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg> },
  // Vertrieb
  { label: "Röstereien", description: "Kunden-CRM und Kontakte", href: "/roasters", category: "Vertrieb", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>, shortcut: "G R" },
  { label: "Deutschland", description: "Deutschlandweiter Vertrieb", href: "/german-sales", category: "Vertrieb", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg> },
  { label: "Aufträge & Abschlüsse", description: "Deals und Verkäufe verfolgen", href: "/deals", category: "Vertrieb", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg> },
  // Logistik
  { label: "Sendungen", description: "Lieferungen und Versand", href: "/shipments", category: "Logistik", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>, shortcut: "G S" },
  // Analyse
  { label: "Analysen", description: "Preise, Prognosen und KPIs", href: "/analytics", category: "Analyse", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg> },
  { label: "KI-Modelle", description: "Machine-Learning Modelle trainieren", href: "/ml", category: "Analyse", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg> },
  { label: "Berichte", description: "Automatische Job-Reports", href: "/reports", category: "Analyse", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg> },
  { label: "Marktnachrichten", description: "Branchennews und Marktinfos", href: "/news", category: "Analyse", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6z"/></svg> },
  { label: "Wissensgraph", description: "Verbindungen zwischen Entitäten", href: "/graph", category: "Analyse", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg> },
  { label: "Stimmungsanalyse", description: "Sentiment der Marktnachrichten", href: "/sentiment", category: "Analyse", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg> },
  // Betrieb
  { label: "Systemstatus", description: "Jobs, Prozesse und Datenqualität", href: "/ops", category: "Betrieb", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg> },
  { label: "Warnungen", description: "Anomalien und Datenprobleme", href: "/alerts", category: "Betrieb", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg> },
  { label: "Duplikatprüfung", description: "Doppelte Einträge zusammenführen", href: "/dedup", category: "Betrieb", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="8" y="8" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> },
  // Suche & KI
  { label: "Volltextsuche", description: "Semantische KI-Suche", href: "/search", category: "Suche & KI", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>, shortcut: "G F" },
  { label: "KI-Analyst", description: "Datenanalysen per KI", href: "/analyst", category: "Suche & KI", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> },
  { label: "KI-Assistent", description: "Chatbot mit Datenzugriff", href: "/assistant", category: "Suche & KI", icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg> },
];

/* ------------------------------------------------------------------ */
/*  Komponente                                                          */
/* ------------------------------------------------------------------ */

export default function CommandPalette({
  forceOpen,
  onForceClose,
}: {
  forceOpen?: boolean;
  onForceClose?: () => void;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const isOpen = open || !!forceOpen;

  const handleClose = () => {
    setOpen(false);
    onForceClose?.();
  };

  // ⌘K / Ctrl+K öffnen
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((o) => !o);
        setQuery("");
        setFocused(0);
      }
      if (e.key === "Escape") handleClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keyboard-Shortcuts G+X
  useEffect(() => {
    let lastKey = "";
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (lastKey === "g" || lastKey === "G") {
        const map: Record<string, string> = {
          d: "/dashboard", c: "/cooperatives", r: "/roasters",
          s: "/shipments", f: "/search",
        };
        if (map[e.key.toLowerCase()]) {
          router.push(map[e.key.toLowerCase()]);
        }
      }
      lastKey = e.key;
      setTimeout(() => { lastKey = ""; }, 800);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [router]);

  useEffect(() => {
    if (isOpen) setTimeout(() => inputRef.current?.focus(), 50);
  }, [isOpen]);

  const filtered = query.trim()
    ? entries.filter(
        (e) =>
          e.label.toLowerCase().includes(query.toLowerCase()) ||
          e.description.toLowerCase().includes(query.toLowerCase()) ||
          e.category.toLowerCase().includes(query.toLowerCase())
      )
    : entries;

  // Gruppierung nach Kategorie
  const categories = Array.from(new Set(filtered.map((e) => e.category)));

  const allFiltered = categories.flatMap((cat) => filtered.filter((e) => e.category === cat));

  const navigate = useCallback(
    (href: string) => {
      handleClose();
      router.push(href);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [router]
  );

  // Tastatur-Navigation
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setFocused((f) => Math.min(f + 1, allFiltered.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setFocused((f) => Math.max(f - 1, 0));
      } else if (e.key === "Enter") {
        const item = allFiltered[focused];
        if (item) navigate(item.href);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, focused, allFiltered, navigate]);

  if (!isOpen) return null;

  let globalIdx = 0;

  return (
    <div className="cmdOverlay" onClick={handleClose}>
      <div className="cmdPanel" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-label="Schnellnavigation">
        {/* Suchfeld */}
        <div className="cmdSearchRow">
          <span className="cmdSearchIcon"><SearchIcon /></span>
          <input
            ref={inputRef}
            className="cmdInput"
            placeholder="Seite oder Aktion suchen..."
            value={query}
            onChange={(e) => { setQuery(e.target.value); setFocused(0); }}
            autoComplete="off"
          />
          <kbd className="cmdKbd">Esc</kbd>
        </div>

        {/* Ergebnisse */}
        <div className="cmdResults">
          {filtered.length === 0 ? (
            <div style={{ padding: "var(--space-8)", textAlign: "center", color: "var(--color-text-muted)", fontSize: "var(--font-size-sm)" }}>
              Keine Ergebnisse für &ldquo;{query}&rdquo;
            </div>
          ) : (
            categories.map((cat) => {
              const items = filtered.filter((e) => e.category === cat);
              return (
                <div key={cat} className="cmdSection">
                  <div className="cmdSectionLabel">{cat}</div>
                  {items.map((item) => {
                    const idx = globalIdx++;
                    return (
                      <button
                        key={item.href}
                        className={`cmdItem ${idx === focused ? "focused" : ""}`}
                        onClick={() => navigate(item.href)}
                        onMouseEnter={() => setFocused(idx)}
                      >
                        <span className="cmdItemIcon">{item.icon}</span>
                        <span className="cmdItemContent">
                          <span className="cmdItemLabel">{item.label}</span>
                          <span className="cmdItemMeta">{item.description}</span>
                        </span>
                        {item.shortcut && (
                          <span className="cmdItemShortcut">{item.shortcut}</span>
                        )}
                        <NavIcon />
                      </button>
                    );
                  })}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="cmdFooter">
          <span className="cmdFooterHint">
            <kbd className="cmdKbd">↑↓</kbd> navigieren
          </span>
          <span className="cmdFooterHint">
            <kbd className="cmdKbd">↵</kbd> öffnen
          </span>
          <span className="cmdFooterHint">
            <kbd className="cmdKbd">Esc</kbd> schließen
          </span>
        </div>
      </div>
    </div>
  );
}
