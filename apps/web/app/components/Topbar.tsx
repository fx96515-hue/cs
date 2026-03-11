"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React from "react";
import CountrySelector from "./CountrySelector";
import { useCountry } from "../hooks/useCountry";

// Page title mapping for breadcrumb context
const pageTitles: Record<string, string> = {
  "/dashboard": "Uebersicht",
  "/search": "Suche",
  "/analyst": "KI-Analyst",
  "/graph": "Knowledge Graph",
  "/peru-sourcing": "Peru Einkauf",
  "/german-sales": "Vertrieb Deutschland",
  "/shipments": "Sendungen",
  "/deals": "Deals & Margen",
  "/analytics": "Analytik & ML",
  "/cooperatives": "Kooperativen",
  "/roasters": "Roestereien",
  "/news": "Marktradar",
  "/reports": "Berichte",
  "/ops": "Betrieb",
  "/alerts": "Warnungen",
  "/dedup": "Duplikate",
  "/ml": "ML-Modelle",
  "/lots": "Lots",
  "/assistant": "Assistent",
  "/sentiment": "Sentiment",
};

function getPageTitle(pathname: string): string {
  // Direct match
  if (pageTitles[pathname]) return pageTitles[pathname];

  // Check for dynamic routes like /cooperatives/[id]
  const basePath = "/" + pathname.split("/")[1];
  if (pageTitles[basePath]) {
    const segments = pathname.split("/").filter(Boolean);
    if (segments.length > 1) {
      return `${pageTitles[basePath]} - Detail`;
    }
    return pageTitles[basePath];
  }

  return "CoffeeStudio";
}

interface TopbarProps {
  authed: boolean;
  onLogout: () => void;
  onMobileMenuClick?: () => void;
}

export default function Topbar({ authed, onLogout, onMobileMenuClick }: TopbarProps) {
  const pathname = usePathname();
  const { selectedCountry, setSelectedCountry, countryConfig } = useCountry();
  const pageTitle = getPageTitle(pathname);

  return (
    <div className="topbar">
      <div className="topbarLeft">
        {/* Mobile menu button */}
        <button
          className="mobileMenuBtn"
          onClick={onMobileMenuClick}
          aria-label="Menu oeffnen"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <div>
          <div className="topbarTitle">{pageTitle}</div>
          <div className="topbarBreadcrumb">
            <Link href="/dashboard" className="link">
              Home
            </Link>
            <span>/</span>
            <span style={{ color: "var(--text)", opacity: 0.9 }}>{pageTitle}</span>
          </div>
        </div>
      </div>

      <div className="topbarRight">
        <CountrySelector value={selectedCountry} onChange={setSelectedCountry} />
        <span
          className="muted small"
          title={countryConfig.data_source.description}
          style={{ display: "none" }}
        >
          {countryConfig.data_source.name}
        </span>

        {authed ? (
          <div className="row" style={{ gap: 8 }}>
            <span className="topbarBadge">Online</span>
            <button className="btn" onClick={onLogout}>
              Abmelden
            </button>
          </div>
        ) : (
          <Link className="btn btnPrimary" href="/login">
            Anmelden
          </Link>
        )}
      </div>
    </div>
  );
}
