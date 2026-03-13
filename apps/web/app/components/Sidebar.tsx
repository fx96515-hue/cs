"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { useState } from "react";
import { setToken } from "../../lib/api";
import { useRouter } from "next/navigation";

interface NavGroup {
  label: string;
  icon: React.ReactNode;
  items?: { href: string; label: string }[];
  href?: string;
}

const ChevronIcon = ({ open }: { open: boolean }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    style={{
      transform: open ? "rotate(180deg)" : "rotate(0deg)",
      transition: "transform 150ms ease",
    }}
  >
    <path
      d="M4 6L8 10L12 6"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const HomeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
);

const SourcingIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2L2 7l10 5 10-5-10-5z"/>
    <path d="M2 17l10 5 10-5"/>
    <path d="M2 12l10 5 10-5"/>
  </svg>
);

const SalesIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="1" x2="12" y2="23"/>
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
  </svg>
);

const LogisticsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="1" y="3" width="15" height="13"/>
    <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
    <circle cx="5.5" cy="18.5" r="2.5"/>
    <circle cx="18.5" cy="18.5" r="2.5"/>
  </svg>
);

const AnalyticsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10"/>
    <line x1="12" y1="20" x2="12" y2="4"/>
    <line x1="6" y1="20" x2="6" y2="14"/>
  </svg>
);

const OpsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
  </svg>
);

const SearchIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);

const LogoutIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/>
    <line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
);

const navGroups: NavGroup[] = [
  {
    label: "Uebersicht",
    icon: <HomeIcon />,
    href: "/dashboard",
  },
  {
    label: "Einkauf",
    icon: <SourcingIcon />,
    items: [
      { href: "/cooperatives", label: "Kooperativen" },
      { href: "/peru-sourcing", label: "Peru Einkauf" },
      { href: "/lots", label: "Lots" },
    ],
  },
  {
    label: "Vertrieb",
    icon: <SalesIcon />,
    items: [
      { href: "/roasters", label: "Roestereien" },
      { href: "/german-sales", label: "Deutschland" },
      { href: "/deals", label: "Deals & Margen" },
    ],
  },
  {
    label: "Logistik",
    icon: <LogisticsIcon />,
    items: [
      { href: "/shipments", label: "Sendungen" },
    ],
  },
  {
    label: "Analyse",
    icon: <AnalyticsIcon />,
    items: [
      { href: "/analytics", label: "Analytik & ML" },
      { href: "/ml", label: "ML-Modelle" },
      { href: "/reports", label: "Berichte" },
      { href: "/news", label: "Marktradar" },
      { href: "/graph", label: "Knowledge Graph" },
    ],
  },
  {
    label: "Betrieb",
    icon: <OpsIcon />,
    items: [
      { href: "/ops", label: "System" },
      { href: "/alerts", label: "Warnungen" },
      { href: "/dedup", label: "Duplikate" },
    ],
  },
  {
    label: "Suche & KI",
    icon: <SearchIcon />,
    items: [
      { href: "/search", label: "Suche" },
      { href: "/analyst", label: "KI-Analyst" },
    ],
  },
];

function NavGroupItem({ group, pathname }: { group: NavGroup; pathname: string }) {
  const hasItems = group.items && group.items.length > 0;
  const isActiveGroup = hasItems
    ? group.items.some((item) => pathname === item.href || pathname.startsWith(item.href + "/"))
    : pathname === group.href || pathname.startsWith((group.href || "") + "/");
  
  const [open, setOpen] = useState(isActiveGroup);

  if (!hasItems && group.href) {
    return (
      <Link
        href={group.href}
        className={`navItem ${isActiveGroup ? "active" : ""}`}
      >
        {group.icon}
        <span>{group.label}</span>
      </Link>
    );
  }

  return (
    <div className="navGroup">
      <button
        className={`navItem navGroupHeader ${isActiveGroup ? "active" : ""}`}
        onClick={() => setOpen((v) => !v)}
        type="button"
      >
        {group.icon}
        <span>{group.label}</span>
        <ChevronIcon open={open} />
      </button>
      {open && group.items && (
        <div className="navSubItems">
          {group.items.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`navSubItem ${active ? "active" : ""}`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function Sidebar({ authed }: { authed: boolean }) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);

  const handleLogout = () => {
    setToken("");
    window.localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <aside className={"sidebar " + (collapsed ? "collapsed" : "")}>
      <div className="brand">
        <div className="logo">CS</div>
        {!collapsed && (
          <div>
            <div className="brandTitle">CoffeeStudio</div>
            <div className="brandSub">Intelligence Platform</div>
          </div>
        )}
      </div>

      <nav className="nav">
        {navGroups.map((group) => (
          <NavGroupItem
            key={group.label}
            group={group}
            pathname={authed ? pathname : "/login"}
          />
        ))}
      </nav>

      <div className="sidebarFooter">
        {authed && (
          <button className="navItem logoutBtn" onClick={handleLogout}>
            <LogoutIcon />
            {!collapsed && <span>Abmelden</span>}
          </button>
        )}
      </div>

      <style jsx>{`
        .navGroup {
          display: flex;
          flex-direction: column;
        }
        .navGroupHeader {
          justify-content: flex-start;
          cursor: pointer;
          background: none;
          width: 100%;
          text-align: left;
        }
        .navGroupHeader span {
          flex: 1;
        }
        .navSubItems {
          display: flex;
          flex-direction: column;
          gap: 2px;
          padding-left: 28px;
          margin-top: 2px;
        }
        .navSubItem {
          display: block;
          padding: 8px 12px;
          font-size: 13px;
          color: var(--muted);
          border-radius: var(--radius-sm);
          transition: all 150ms ease;
        }
        .navSubItem:hover {
          color: var(--text);
          background: var(--panel-2);
        }
        .navSubItem.active {
          color: var(--text);
          background: var(--panel-3);
          font-weight: 500;
        }
        .logoutBtn {
          width: 100%;
          color: var(--muted);
          border: 1px solid var(--border);
          background: var(--panel-2);
          cursor: pointer;
        }
        .logoutBtn:hover {
          color: var(--accent-3);
          border-color: rgba(196, 90, 74, 0.3);
          background: rgba(196, 90, 74, 0.08);
        }
      `}</style>
    </aside>
  );
}
