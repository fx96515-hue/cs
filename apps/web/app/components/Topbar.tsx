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
    <div className="topbar">
      <div className="topbarLeft">
        <div className="topbarTitle">Steuerzentrale</div>
        <div className="pill">Daten | Workflows | Qualitaet</div>
      </div>
      <div className="topbarRight">
        <CountrySelector value={selectedCountry} onChange={setSelectedCountry} />
        <span className="muted small" title={countryConfig.data_source.description}>
          {countryConfig.data_source.name}
        </span>
        {authed ? (
          <button className="btn" onClick={onLogout}>
            Abmelden
          </button>
        ) : (
          <Link className="btn btnPrimary" href="/login">
            Anmelden
          </Link>
        )}
      </div>
    </div>
  );
}
