"use client";

import React from "react";
import { SupportedCountry, SUPPORTED_COUNTRIES, COUNTRY_CONFIGS } from "../types";

interface CountrySelectorProps {
  value: SupportedCountry;
  onChange: (country: SupportedCountry) => void;
  className?: string;
}

/**
 * Country selector dropdown for switching between supported origin countries.
 * Displays flag emoji, country name and currency code for each option.
 */
export default function CountrySelector({ value, onChange, className }: CountrySelectorProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as SupportedCountry)}
      className={className}
      title="Herkunftsland wählen"
      style={{
        background: "var(--surface, #1e293b)",
        color: "var(--text, #f1f5f9)",
        border: "1px solid var(--border, #334155)",
        borderRadius: 6,
        padding: "4px 8px",
        fontSize: 13,
        cursor: "pointer",
      }}
    >
      {SUPPORTED_COUNTRIES.map((code) => {
        const cfg = COUNTRY_CONFIGS[code];
        return (
          <option key={code} value={code}>
            {(cfg.flag_emoji ? cfg.flag_emoji + " " : "") + code + " – " + cfg.name + " (" + cfg.currency + ")"}
          </option>
        );
      })}
    </select>
  );
}
