# Domain: cuppings

## Purpose
Owns business logic and API contracts for the **cuppings** capability.

## Structure
### API
- `routes.py`

### Schemas
- `cupping.py`

### Services
- (none)

## Boundaries
- Keep route handlers thin and push logic into services where possible.
- Keep request/response contracts in domain-local schemas.
- Expose compatibility wrappers only for migration safety, not new internal imports.

## Dependency Rules
- Prefer imports from `app.domains.cuppings.*` inside this domain.
- Cross-domain usage should call stable service APIs, not reach into route modules.

## Validation
- Covered by global backend gates: `ruff`, `mypy`, and `pytest apps/api/tests`.
