"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import React, { useState, useEffect } from "react";
import { setToken } from "../../lib/api";

/* ============================================================
   ENTERPRISE SIDEBAR - PROFESSIONAL NAVIGATION
   ============================================================ */

const ChevronIcon = ({ open }: { open: boolean }) => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 14 14"
    fill="none"
    style={{
      transform: open ? "rotate(180deg)" : "rotate(0deg)",
      transition: "transform 200ms cubic-bezier(0.4, 0, 0.2, 1)",
      flexShrink: 0,
    }}
  >
    <path
      d="M3.5 5.25L7 8.75L10.5 5.25"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/* Icon Set - Consistent 20x20 with 1.5px stroke */
const icons = {
  dashboard: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="9" rx="1"/>
      <rect x="14" y="3" width="7" height="5" rx="1"/>
      <rect x="14" y="12" width="7" height="9" rx="1"/>
      <rect x="3" y="16" width="7" height="5" rx="1"/>
    </svg>
  ),
  sourcing: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L2 7l10 5 10-5-10-5z"/>
      <path d="M2 17l10 5 10-5"/>
      <path d="M2 12l10 5 10-5"/>
    </svg>
  ),
  sales: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
      <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  ),
  logistics: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1" y="3" width="15" height="13" rx="1"/>
      <path d="M16 8h4l3 3v5h-7V8z"/>
      <circle cx="5.5" cy="18.5" r="2.5"/>
      <circle cx="18.5" cy="18.5" r="2.5"/>
    </svg>
  ),
  analytics: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 21H4.6c-.56 0-.84 0-1.054-.109a1 1 0 0 1-.437-.437C3 20.24 3 19.96 3 19.4V3"/>
      <path d="M7 14l4-4 4 4 6-6"/>
    </svg>
  ),
  operations: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
    </svg>
  ),
  ai: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <path d="M21 21l-4.35-4.35"/>
      <path d="M11 8v6M8 11h6"/>
    </svg>
  ),
  logout: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
  ),
};

/* Sub-item icons - smaller, 16x16 */
const subIcons = {
  cooperatives: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3"/>
    </svg>
  ),
  peru: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>
      <path d="M2 12h20"/>
    </svg>
  ),
  lots: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
    </svg>
  ),
  roasters: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8h1a4 4 0 0 1 0 8h-1"/>
      <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/>
      <line x1="6" y1="1" x2="6" y2="4"/>
      <line x1="10" y1="1" x2="10" y2="4"/>
      <line x1="14" y1="1" x2="14" y2="4"/>
    </svg>
  ),
  germany: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 21v-4m0 0V5a2 2 0 0 1 2-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 0 0-2 2z"/>
    </svg>
  ),
  deals: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
    </svg>
  ),
  shipments: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1" y="6" width="22" height="12" rx="2"/>
      <path d="M1 10h22"/>
    </svg>
  ),
  analytics: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/>
      <line x1="12" y1="20" x2="12" y2="4"/>
      <line x1="6" y1="20" x2="6" y2="14"/>
    </svg>
  ),
  ml: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2M7.5 13A1.5 1.5 0 0 0 6 14.5 1.5 1.5 0 0 0 7.5 16 1.5 1.5 0 0 0 9 14.5 1.5 1.5 0 0 0 7.5 13m9 0a1.5 1.5 0 0 0-1.5 1.5 1.5 1.5 0 0 0 1.5 1.5 1.5 1.5 0 0 0 1.5-1.5 1.5 1.5 0 0 0-1.5-1.5"/>
    </svg>
  ),
  reports: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
    </svg>
  ),
  news: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v1m2 13a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2z"/>
    </svg>
  ),
  graph: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="2"/>
      <circle cx="6" cy="6" r="2"/>
      <circle cx="18" cy="6" r="2"/>
      <circle cx="6" cy="18" r="2"/>
      <circle cx="18" cy="18" r="2"/>
      <path d="M12 10V8M7.5 7.5l3 3M16.5 7.5l-3 3M7.5 16.5l3-3M16.5 16.5l-3-3"/>
    </svg>
  ),
  sentiment: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
      <line x1="9" y1="9" x2="9.01" y2="9"/>
      <line x1="15" y1="9" x2="15.01" y2="9"/>
    </svg>
  ),
  system: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2"/>
      <line x1="8" y1="21" x2="16" y2="21"/>
      <line x1="12" y1="17" x2="12" y2="21"/>
    </svg>
  ),
  alerts: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>
  ),
  dedup: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="8" y="2" width="8" height="4" rx="1"/>
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
      <path d="M9 12l2 2 4-4"/>
    </svg>
  ),
  search: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
  ),
  analyst: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      <path d="M8 10h.01M12 10h.01M16 10h.01"/>
    </svg>
  ),
  assistant: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
  ),
};

/* Navigation Structure */
interface NavItem {
  href: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string;
}

interface NavGroup {
  label: string;
  icon: React.ReactNode;
  items?: NavItem[];
  href?: string;
}

const navGroups: NavGroup[] = [
  {
    label: "Dashboard",
    icon: icons.dashboard,
    href: "/dashboard",
  },
  {
    label: "Einkauf",
    icon: icons.sourcing,
    items: [
      { href: "/cooperatives", label: "Kooperativen", icon: subIcons.cooperatives },
      { href: "/peru-sourcing", label: "Peru Einkauf", icon: subIcons.peru },
      { href: "/lots", label: "Kaffee-Partien", icon: subIcons.lots },
    ],
  },
  {
    label: "Vertrieb",
    icon: icons.sales,
    items: [
      { href: "/roasters", label: "Röstereien", icon: subIcons.roasters },
      { href: "/german-sales", label: "Deutschland", icon: subIcons.germany },
      { href: "/deals", label: "Aufträge & Abschlüsse", icon: subIcons.deals },
    ],
  },
  {
    label: "Logistik",
    icon: icons.logistics,
    items: [
      { href: "/shipments", label: "Sendungen", icon: subIcons.shipments },
    ],
  },
  {
    label: "Analyse",
    icon: icons.analytics,
    items: [
      { href: "/analytics", label: "Analysen", icon: subIcons.analytics },
      { href: "/ml", label: "KI-Modelle", icon: subIcons.ml },
      { href: "/reports", label: "Berichte", icon: subIcons.reports },
      { href: "/news", label: "Marktnachrichten", icon: subIcons.news },
      { href: "/graph", label: "Wissensgraph", icon: subIcons.graph },
      { href: "/sentiment", label: "Stimmungsanalyse", icon: subIcons.sentiment },
    ],
  },
  {
    label: "Betrieb",
    icon: icons.operations,
    items: [
      { href: "/ops", label: "Systemstatus", icon: subIcons.system },
      { href: "/alerts", label: "Warnungen", icon: subIcons.alerts },
      { href: "/dedup", label: "Duplikatprüfung", icon: subIcons.dedup },
    ],
  },
  {
    label: "Suche & KI",
    icon: icons.ai,
    items: [
      { href: "/search", label: "Volltextsuche", icon: subIcons.search },
      { href: "/analyst", label: "KI-Analyst", icon: subIcons.analyst },
      { href: "/assistant", label: "KI-Assistent", icon: subIcons.assistant },
    ],
  },
];

/* NavGroup Component */
function NavGroupItem({ 
  group, 
  pathname,
  expandedGroups,
  toggleGroup,
}: { 
  group: NavGroup; 
  pathname: string;
  expandedGroups: Set<string>;
  toggleGroup: (label: string) => void;
}) {
  const hasItems = group.items && group.items.length > 0;
  const isActiveGroup = hasItems
    ? group.items.some((item) => pathname === item.href || pathname.startsWith(item.href + "/"))
    : pathname === group.href || pathname.startsWith((group.href || "") + "/");
  
  const isOpen = expandedGroups.has(group.label);

  // Direct link (no subitems)
  if (!hasItems && group.href) {
    return (
      <Link href={group.href} className={`sidebarNavLink ${isActiveGroup ? "active" : ""}`}>
        <span className="sidebarNavIcon">{group.icon}</span>
        <span className="sidebarNavLabel">{group.label}</span>
      </Link>
    );
  }

  // Collapsible group
  return (
    <div className="sidebarNavGroup">
      <button
        className={`sidebarNavLink ${isActiveGroup ? "active" : ""}`}
        onClick={() => toggleGroup(group.label)}
        type="button"
        aria-expanded={isOpen}
      >
        <span className="sidebarNavIcon">{group.icon}</span>
        <span className="sidebarNavLabel">{group.label}</span>
        <span className="sidebarNavChevron">
          <ChevronIcon open={isOpen} />
        </span>
      </button>
      
      <div className={`sidebarSubNav ${isOpen ? "open" : ""}`}>
        {group.items?.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebarSubLink ${active ? "active" : ""}`}
            >
              {item.icon && <span className="sidebarSubIcon">{item.icon}</span>}
              <span className="sidebarSubLabel">{item.label}</span>
              {item.badge && <span className="sidebarSubBadge">{item.badge}</span>}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

/* Main Sidebar Component */
export default function Sidebar({ authed }: { authed: boolean }) {
  const pathname = usePathname();
  const router = useRouter();
  
  // Initialize expanded groups based on current path
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    navGroups.forEach(group => {
      if (group.items?.some(item => pathname === item.href || pathname.startsWith(item.href + "/"))) {
        initial.add(group.label);
      }
    });
    return initial;
  });

  // Update expanded groups when pathname changes
  useEffect(() => {
    navGroups.forEach(group => {
      if (group.items?.some(item => pathname === item.href || pathname.startsWith(item.href + "/"))) {
        setExpandedGroups(prev => new Set(prev).add(group.label));
      }
    });
  }, [pathname]);

  const toggleGroup = (label: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  };

  const handleLogout = () => {
    setToken("");
    window.localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <aside className="sidebarContainer">
      {/* Brand Header */}
      <div className="sidebarBrand">
        <div className="sidebarLogo">
          <span>CS</span>
        </div>
        <div className="sidebarBrandText">
          <div className="sidebarBrandTitle">CoffeeStudio</div>
          <div className="sidebarBrandSub">Intelligente Plattform</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebarNav">
        {/* Dashboard */}
        <div className="sidebarNavSection">
          {navGroups.slice(0, 1).map((group) => (
            <NavGroupItem 
              key={group.label} 
              group={group} 
              pathname={authed ? pathname : "/login"}
              expandedGroups={expandedGroups}
              toggleGroup={toggleGroup}
            />
          ))}
        </div>
        
        {/* Kernmodule: Einkauf, Vertrieb, Logistik */}
        <div className="sidebarNavDivider">
          <span>Kernmodule</span>
        </div>
        
        <div className="sidebarNavSection">
          {navGroups.slice(1, 4).map((group) => (
            <NavGroupItem 
              key={group.label} 
              group={group} 
              pathname={authed ? pathname : "/login"}
              expandedGroups={expandedGroups}
              toggleGroup={toggleGroup}
            />
          ))}
        </div>
        
        {/* Analyse & Betrieb */}
        <div className="sidebarNavDivider">
          <span>Analyse & Betrieb</span>
        </div>
        
        <div className="sidebarNavSection">
          {navGroups.slice(4, 6).map((group) => (
            <NavGroupItem 
              key={group.label} 
              group={group} 
              pathname={authed ? pathname : "/login"}
              expandedGroups={expandedGroups}
              toggleGroup={toggleGroup}
            />
          ))}
        </div>
        
        {/* Suche & KI */}
        <div className="sidebarNavDivider">
          <span>Suche & KI</span>
        </div>
        
        <div className="sidebarNavSection">
          {navGroups.slice(6).map((group) => (
            <NavGroupItem 
              key={group.label} 
              group={group} 
              pathname={authed ? pathname : "/login"}
              expandedGroups={expandedGroups}
              toggleGroup={toggleGroup}
            />
          ))}
        </div>
      </nav>

      {/* Footer */}
      {authed && (
        <div className="sidebarFooter">
          <button className="sidebarLogout" onClick={handleLogout} type="button">
            <span className="sidebarNavIcon">{icons.logout}</span>
            <span>Abmelden</span>
          </button>
        </div>
      )}
    </aside>
  );
}
