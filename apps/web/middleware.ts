/**
 * middleware.ts
 * Route-Guard: vorbereitet für httpOnly-Cookie-Auth (Roadbook Schritt 2).
 *
 * AKTUELL DEAKTIVIERT — Auth läuft noch über localStorage (AppShell-Guard).
 * Aktivieren sobald das Backend /api/auth/login einen httpOnly-Cookie setzt.
 *
 * Zum Aktivieren: Kommentar um den Guard-Block entfernen.
 */
import { NextRequest, NextResponse } from "next/server";

export function middleware(_req: NextRequest) {
  // Guard deaktiviert – AppShell übernimmt Client-seitigen Schutz
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
