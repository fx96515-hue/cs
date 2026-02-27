"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function hasToken(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(localStorage.getItem("token"));
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authed, setAuthed] = React.useState(false);

  React.useEffect(() => {
    setAuthed(hasToken());
  }, [pathname]);

  // Keep login page clean (no chrome)
  if (pathname === "/login") {
    return <div className="center">{children}</div>;
  }

  return (
    <div className="shell">
      <Sidebar authed={authed} />
      <div className="main">
        <Topbar
          authed={authed}
          onLogout={() => {
            localStorage.removeItem("token");
            setAuthed(false);
            router.push("/login");
          }}
        />
        <div className="content">{children}</div>
      </div>
    </div>
  );
}
