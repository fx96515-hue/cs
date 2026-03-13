"use client";

import Link from "next/link";
import React from "react";
import CountrySelector from "./CountrySelector";
import { useCountry } from "../hooks/useCountry";

export default function Topbar({
  authed,
  onLogout,
}: {
  authed: boolean;
  onLogout: () => void;
}) {
  const { selectedCountry, setSelectedCountry, countryConfig } = useCountry();

  return (
    <header className="topbar">
      <div className="topbarLeft">
        <h1 className="topbarTitle">Steuerzentrale</h1>
        <div className="topbarMeta">
          <span>Daten</span>
          <span className="topbarDot" aria-hidden="true" />
          <span>Workflows</span>
          <span className="topbarDot" aria-hidden="true" />
          <span>Qualitaet</span>
        </div>
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
        .topbarMeta {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 4px 12px;
          background: var(--color-bg-subtle);
          border-radius: var(--radius-full);
          font-size: 12px;
          color: var(--color-text-muted);
        }
        .topbarDot {
          width: 3px;
          height: 3px;
          border-radius: 50%;
          background: var(--color-border-strong);
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
