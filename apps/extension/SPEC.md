# Obee — CoffeeStudio Chrome Extension (Spec)

> Status: **MVP implemented** (phase 1). Phases 2–3 are planned.
> Binding repo rules: see root `ARBEITSANWEISUNG.md`.

## Purpose

Obee lets a user clip a roaster's website straight into CoffeeStudio while
browsing — review the auto-extracted details, then save them as a roaster
record via the existing API. No scraping pipeline, no Docker: a lean
Manifest V3 extension that talks to the FastAPI backend over HTTP.

## Design principles

- **Lean:** Manifest V3 + plain TypeScript, bundled with **esbuild**. Three dev
  dependencies (`esbuild`, `typescript`, `@types/chrome`). No framework, no WXT,
  no Docker.
- **Backend-only via HTTP:** the extension consumes the existing API; it adds
  **no** backend code. Network + token handling live in the background service
  worker, which has `host_permissions` for the API origin, so requests are not
  subject to page CORS — **no backend CORS change is required**.
- **Honest data:** extracted fields are heuristics shown in an editable form;
  the user confirms before anything is written. Clipped text is rendered with
  `textContent` (never interpolated as HTML).

## Architecture

```
popup (UI)  ──messages──►  background service worker  ──fetch──►  CoffeeStudio API
                                  │
                                  └─ chrome.scripting.executeScript ─► active tab (extract)
```

- `src/popup/*` — UI; talks only to the worker via the typed `send()` helper.
- `src/background.ts` — owns the JWT, dispatches messages, injects the
  self-contained page extractor on demand.
- `src/lib/{api,auth,messages,types}.ts` — API client, token/config storage,
  message protocol, shared types.

## API contracts used (apps/api)

| Action        | Endpoint            | Notes |
| ------------- | ------------------- | ----- |
| Sign in       | `POST /auth/login`  | JSON `{email, password}` → `{access_token}` (5/min limit) |
| Validate      | `GET /auth/me`      | Bearer; returns `{id,email,role,is_active}` |
| Save roaster  | `POST /roasters/`   | Bearer; role `admin`/`analyst`; `RoasterCreate` |

The source URL, page title and `source: "obee"` are stored in the roaster's
free-form `meta` field for provenance.

## Auth & storage

- JWT in `chrome.storage.session` (cleared on browser close).
- API base URL + last email in `chrome.storage.local` (non-secret).
- Default base URL `http://localhost:8000`, editable in **Settings**.

## Permissions

`activeTab`, `scripting`, `storage`; `host_permissions` for
`http://localhost:8000/*` and `http://127.0.0.1:8000/*`.

## Build / dev

```bash
cd apps/extension
npm install
npm run build      # -> dist/  (load as unpacked extension)
npm run dev        # watch mode
npm run lint       # tsc --noEmit (type gate)
```

## Roadmap / open items

- **Phase 2:** Assistant side panel backed by `POST /assistant`.
- **Phase 3:** Market/price overlay backed by `/market`.
- Clip **cooperatives** as well as roasters (`/cooperatives`).
- Configurable production host (`optional_host_permissions` + request flow)
  instead of pinned localhost hosts.
- Dedup hint via `/dedup` before saving.
- Add a CI workflow (mirror `ci-frontend.yml`) once repo Actions are restored;
  add unit tests for the extractor and API client.
