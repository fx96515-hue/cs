// Lean build for the Obee extension: esbuild bundles the TypeScript entrypoints,
// then static assets (manifest, popup HTML/CSS, icons) are copied into dist/.
// Usage: `node build.mjs` (one-shot) or `node build.mjs --watch` (rebuild on change).
import { build, context } from "esbuild";
import { cp, mkdir, rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const outdir = resolve(root, "dist");
const watch = process.argv.includes("--watch");

const entryPoints = {
  background: resolve(root, "src/background.ts"),
  "popup/popup": resolve(root, "src/popup/popup.ts"),
  "sidepanel/sidepanel": resolve(root, "src/sidepanel/sidepanel.ts"),
};

/** Copy the static assets the bundler does not touch. */
async function copyStatic() {
  await cp(resolve(root, "src/manifest.json"), resolve(outdir, "manifest.json"));
  await cp(resolve(root, "src/popup/popup.html"), resolve(outdir, "popup/popup.html"));
  await cp(resolve(root, "src/popup/popup.css"), resolve(outdir, "popup/popup.css"));
  await cp(resolve(root, "src/sidepanel/sidepanel.html"), resolve(outdir, "sidepanel/sidepanel.html"));
  await cp(resolve(root, "src/sidepanel/sidepanel.css"), resolve(outdir, "sidepanel/sidepanel.css"));
  await cp(resolve(root, "src/icons"), resolve(outdir, "icons"), { recursive: true });
}

const options = {
  entryPoints,
  outdir,
  bundle: true,
  format: "esm",
  target: "chrome116",
  sourcemap: watch ? "inline" : false,
  minify: !watch,
  logLevel: "info",
};

await rm(outdir, { recursive: true, force: true });
await mkdir(outdir, { recursive: true });

if (watch) {
  const ctx = await context(options);
  await ctx.rebuild();
  await copyStatic();
  await ctx.watch();
  console.log("[obee] watching for changes — load apps/extension/dist as an unpacked extension");
} else {
  await build(options);
  await copyStatic();
  console.log("[obee] build complete -> apps/extension/dist");
}
