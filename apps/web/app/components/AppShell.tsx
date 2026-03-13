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
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar authed={authed} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Topbar
          authed={authed}
          onLogout={() => {
            localStorage.removeItem("token");
            setAuthed(false);
            router.push("/login");
          }}
        />
        <div className="flex-1 overflow-auto">{children}</div>
      </div>
    </div>
  );
}
