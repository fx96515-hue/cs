"use client";

import Link from "next/link";
import React from "react";
import CountrySelector from "./CountrySelector";
import { useCountry } from "../hooks/useCountry";

interface TopbarProps {
  authed: boolean;
  onLogout: () => void;
  onOpenCmd?: () => void;
}

export default function Topbar({ authed, onLogout, onOpenCmd }: TopbarProps) {
  const { selectedCountry, setSelectedCountry, countryConfig } = useCountry();
  const isMac = typeof navigator !== "undefined" && /Mac/.test(navigator.platform);
  const shortcut = isMac ? "⌘K" : "Ctrl+K";

  return (
    <header className="topbar">
      <div className="topbarLeft">
        {/* Suchleiste / Command-Palette Trigger */}
        <button
          className="topbarSearch"
          onClick={onOpenCmd}
          type="button"
          aria-label="Schnellsuche öffnen"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <span>Suchen...</span>
          <kbd className="topbarKbd">{shortcut}</kbd>
        </button>
      </div>

      <div className="topbarRight">
        <CountrySelector value={selectedCountry} onChange={setSelectedCountry} />
        <span className="topbarSource" title={countryConfig.data_source.description}>
          {countryConfig.data_source.name}
        </span>
        {authed ? (
          <button className="btn btnGhost btnSm" onClick={onLogout} type="button">
            Abmelden
          </button>
        ) : (
          <Link className="btn btnPrimary btnSm" href="/login">
            Anmelden
          </Link>
        )}
      </div>

      <style jsx>{`
        .topbarSearch {
          display: flex;
          align-items: center;
          gap: 8px;
          height: 36px;
          padding: 0 14px;
          border-radius: var(--radius-md);
          border: 1px solid var(--color-border-strong);
          background: var(--color-bg-subtle);
          color: var(--color-text-muted);
          cursor: pointer;
          font-size: var(--font-size-sm);
          font-family: var(--font-family);
          transition: all var(--transition-fast);
          min-width: 220px;
        }
        .topbarSearch span {
          flex: 1;
          text-align: left;
        }
        .topbarSearch:hover {
          border-color: var(--color-border-strong);
          background: var(--color-bg-muted);
          color: var(--color-text-secondary);
        }
        .topbarKbd {
          font-size: 11px;
          padding: 2px 6px;
          border-radius: 4px;
          background: var(--color-surface);
          border: 1px solid var(--color-border-strong);
          color: var(--color-text-muted);
          font-family: var(--font-mono);
          flex-shrink: 0;
        }
        .topbarSource {
          font-size: 12px;
          color: var(--color-text-muted);
          padding: 4px 10px;
          background: var(--color-bg-subtle);
          border-radius: var(--radius-sm);
        }
      `}</style>
    </header>
  );
}
