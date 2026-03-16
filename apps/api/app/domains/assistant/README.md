# Domain: assistant

## Purpose
Owns business logic and API contracts for the **assistant** capability.

## Structure
### API
- `analyst_routes.py`
- `chat_routes.py`

### Schemas
- `analyst.py`
- `chat.py`

### Services
- `analyst_service.py`
- `chat_service.py`

## Boundaries
- Keep route handlers thin and push logic into services where possible.
- Keep request/response contracts in domain-local schemas.
- Expose compatibility wrappers only for migration safety, not new internal imports.

## Dependency Rules
- Prefer imports from `app.domains.assistant.*` inside this domain.
- Cross-domain usage should call stable service APIs, not reach into route modules.

## Validation
- Covered by global backend gates: `ruff`, `mypy`, and `pytest apps/api/tests`.
