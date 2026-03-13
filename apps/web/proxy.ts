/**
 * proxy.ts — Route-Guard (aktuell passthrough)
 * Vorbereitet für httpOnly-Cookie-Auth (ENTERPRISE_ROADBOOK.md Schritt 2).
 * Auth läuft noch über localStorage → AppShell-Guard übernimmt.
 */
import { type NextRequest, NextResponse } from "next/server";

export function proxy(req: NextRequest) {
  void req;
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard", "/roasters/:path*", "/cooperatives/:path*"],
};
