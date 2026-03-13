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
    <div className="border-b border-border bg-card sticky top-0 z-40 h-16">
      <div className="flex items-center justify-between h-full px-6 gap-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="text-lg font-semibold text-foreground">Steuerzentrale</div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary text-xs font-medium text-secondary-foreground">
            <span>Daten</span>
            <span className="text-muted-foreground">|</span>
            <span>Workflows</span>
            <span className="text-muted-foreground">|</span>
            <span>Qualität</span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <CountrySelector value={selectedCountry} onChange={setSelectedCountry} />
          <span className="text-xs text-muted-foreground" title={countryConfig.data_source.description}>
            {countryConfig.data_source.name}
          </span>
          {authed ? (
            <button 
              className="px-3 py-1.5 rounded-md bg-muted text-foreground text-sm font-medium hover:bg-muted/80 transition-colors"
              onClick={onLogout}
            >
              Abmelden
            </button>
          ) : (
            <Link 
              className="px-4 py-1.5 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
              href="/login"
            >
              Anmelden
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
