/** @type {import('next').NextConfig} */
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const nextConfig = {
  output: "standalone",
  turbopack: {
    root: __dirname,
    resolveAlias: {
      // ErrorPanel.tsx wurde in AlertError.tsx umbenannt.
      // Dieser Alias sorgt dafuer dass alter Turbopack-Cache-Eintraege
      // auf die neue Datei zeigen, ohne dass ErrorPanel.tsx existieren muss.
      "../components/ErrorPanel": path.join(__dirname, "app/components/AlertError"),
      "./components/ErrorPanel": path.join(__dirname, "app/components/AlertError"),
    },
  },
};

export default nextConfig;
