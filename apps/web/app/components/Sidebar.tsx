"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React from "react";

const items: { href: string; label: string; badge?: string }[] = [
  { href: "/dashboard", label: "Übersicht" },
  { href: "/search", label: "🔍 Suche" },
  { href: "/analyst", label: "🤖 KI-Analyst" },
  { href: "/graph", label: "🕸️ Knowledge Graph" },
  { href: "/peru-sourcing", label: "Peru Einkauf" },
  { href: "/german-sales", label: "Vertrieb Deutschland" },
  { href: "/shipments", label: "Sendungen" },
  { href: "/deals", label: "Deals & Margen" },
  { href: "/analytics", label: "Analytik & ML" },
  { href: "/cooperatives", label: "Kooperativen" },
  { href: "/roasters", label: "Röstereien" },
  { href: "/news", label: "Marktradar" },
  { href: "/reports", label: "Berichte" },
  { href: "/ops", label: "Betrieb" },
  { href: "/alerts", label: "Warnungen" },
  { href: "/dedup", label: "Duplikate" },
  { href: "/ml", label: "ML-Modelle" },
];

export default function Sidebar({ authed }: { authed: boolean }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);

  return (
    <aside className={"sidebar " + (collapsed ? "collapsed" : "")}> 
      <div className="brand">
        <div className="logo">CS</div>
        {!collapsed && (
          <div>
            <div className="brandTitle">CoffeeStudio</div>
            <div className="brandSub">Option D • MAXSTACK</div>
          </div>
        )}
      </div>

      <button className="ghost" onClick={() => setCollapsed((v) => !v)}>
        {collapsed ? "»" : "«"}
      </button>

      <nav className="nav">
        {items.map((it) => {
          const active = pathname === it.href || (it.href !== "/" && pathname?.startsWith(it.href + "/"));
          return (
            <Link key={it.href} href={authed ? it.href : "/login"} className={"navItem " + (active ? "active" : "")}> 
              <span>{it.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="sidebarFooter">
        {!collapsed && (
          <div className="muted small">
            Tipp: Öffne <span className="mono">http://traefik.localhost/dashboard/</span> für Routing-Checks.
          </div>
        )}
      </div>
    </aside>
  );
}
