# Obee — CoffeeStudio Clipper

A lean Manifest V3 Chrome extension that clips roaster pages into CoffeeStudio.
Plain TypeScript bundled with esbuild — no framework, no Docker. See
[`SPEC.md`](SPEC.md) for design details and the roadmap.

## Quick start

```bash
cd apps/extension
npm install
npm run build
```

Then load it in Chrome:

1. Open `chrome://extensions`, enable **Developer mode**.
2. **Load unpacked** → select `apps/extension/dist`.
3. Make sure the CoffeeStudio API is running (default `http://localhost:8000`).
4. Click the Obee icon → **Sign in** with your CoffeeStudio account.
5. On a roaster's site, open Obee → **Read this page** → review → **Save**.

Change the API base URL anytime under **Settings** in the popup.

## Scripts

| Command            | Purpose                                  |
| ------------------ | ---------------------------------------- |
| `npm run build`    | Production build into `dist/`            |
| `npm run dev`      | Rebuild on change (watch)                |
| `npm run lint`     | Type-check gate (`tsc --noEmit`)         |
| `npm run typecheck`| Same as lint                             |
| `npm run clean`    | Remove `dist/`                           |

## Notes

- The JWT is kept in `chrome.storage.session` and cleared when the browser
  closes. Only non-secret config (API URL, last email) is persisted locally.
- All API calls go through the background service worker, which holds
  `host_permissions` for the API origin — so no backend CORS change is needed
  for local development. To target a non-localhost API, add its origin to
  `host_permissions` in `src/manifest.json`.
