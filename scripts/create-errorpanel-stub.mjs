// Creates ErrorPanel.tsx as a stub that re-exports from AlertError.tsx
// This is needed because Turbopack has a stale cache entry for ErrorPanel.tsx
import { writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const dest = join(__dirname, "../apps/web/app/components/ErrorPanel.tsx");

const content = `"use client";
// ErrorPanel.tsx — Stub fuer Rueckwaertskompatibilitaet
// Echte Implementierung liegt in AlertError.tsx
export { ErrorPanel } from "./AlertError";
`;

writeFileSync(dest, content, "utf8");
console.log("[v0] Created:", dest);
