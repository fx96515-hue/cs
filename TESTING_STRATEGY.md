# Testing Strategy

## Core Gates

Backend:

- auth
- rate limiting
- PR721 dashboard adapters
- semantic search
- scheduler dashboard routes
- market dashboard routes
- monitoring dashboard routes

Frontend:

- production build via `npm run build`

## Intent

The current strategy optimizes for safe PR721 integration:

- protect existing auth and security behavior
- verify new dashboard adapters return stable payloads
- keep frontend compilation and route generation green
- avoid broad schema or provider regressions

## Recommended Follow-Up

- add targeted integration tests for the new additive provider catalog
- add migration smoke on a disposable database
- add UI smoke for `pipeline`, `features`, `markt`, `scheduler`, `ki`
