"use client";

import Link from "next/link";
import { useState } from "react";
import { getToken, setToken } from "../../lib/api";
import { usePathname, useRouter } from "next/navigation";

function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const active = pathname === href || pathname?.startsWith(href + "/");
  return (
    <Link
      href={href}
      style={{
        textDecoration: "none",
        padding: "6px 10px",
        borderRadius: 8,
        border: "1px solid #eee",
        background: active ? "#f6f6f6" : "white",
        color: "#111",
      }}
    >
      {label}
    </Link>
  );
}

export default function Nav() {
  const [hasToken] = useState(() => !!getToken());
  const router = useRouter();

  if (!hasToken) return null;

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
      <NavLink href="/dashboard" label="Dashboard" />
      <NavLink href="/cooperatives" label="Kooperativen" />
      <NavLink href="/roasters" label="Röster" />
      <NavLink href="/lots" label="Lots" />
      <NavLink href="/reports" label="Reports" />
      <NavLink href="/search" label="Suche 🔍" />

      <div style={{ flex: 1 }} />

      <button
        onClick={() => {
          setToken("");
          window.localStorage.removeItem("token");
          router.push("/login");
        }}
        style={{
          padding: "6px 10px",
          borderRadius: 8,
          border: "1px solid #eee",
          background: "white",
          cursor: "pointer",
        }}
      >
        Logout
      </button>
    </div>
  );
}
