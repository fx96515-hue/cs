# Domain: auto_outreach

## Purpose
Owns business logic and API contracts for the **auto_outreach** capability.

## Structure
### API
- `routes.py`

### Schemas
- `auto_outreach.py`

### Services
- `campaigns.py`

## Boundaries
- Keep route handlers thin and push logic into services where possible.
- Keep request/response contracts in domain-local schemas.
- Expose compatibility wrappers only for migration safety, not new internal imports.

## Dependency Rules
- Prefer imports from `app.domains.auto_outreach.*` inside this domain.
- Cross-domain usage should call stable service APIs, not reach into route modules.

## Validation
- Covered by global backend gates: `ruff`, `mypy`, and `pytest apps/api/tests`.
