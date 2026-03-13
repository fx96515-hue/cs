/**
 * middleware.ts
 * Next.js Route-Guard: schützt alle Seiten außer /login.
 *
 * Wichtig: middleware läuft auf dem Edge-Runtime (kein Zugriff auf localStorage).
 * Der Token wird daher als Cookie "token" erwartet. Das Login-Flow muss
 * diesen Cookie beim Anmelden setzen (siehe /api/auth/login route).
 *
 * Solange nur localStorage verwendet wird (aktueller Stand), greift dieser
 * Guard nicht — er ist vorbereitet für den httpOnly-Cookie-Umstieg (Roadbook Schritt 2).
 * Ohne Cookie läuft der Request durch; AppShell übernimmt dann den Client-Guard.
 */
import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/api/auth"];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Öffentliche Pfade immer durchlassen
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Statische Dateien und Next.js-Internals durchlassen
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Token aus Cookie lesen (httpOnly-Cookie-Phase)
  const token = req.cookies.get("token")?.value;

  // Kein Token → auf Login umleiten
  if (!token) {
    const loginUrl = req.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Middleware auf alle Seiten außer statischen Dateien anwenden
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
