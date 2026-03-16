# Domain: price_quotes

## Purpose
Owns business logic and API contracts for the **price_quotes** capability.

## Structure
### API
- `routes.py`

### Schemas
- `price_quote.py`

### Services
- (none)

## Boundaries
- Keep route handlers thin and push logic into services where possible.
- Keep request/response contracts in domain-local schemas.
- Expose compatibility wrappers only for migration safety, not new internal imports.

## Dependency Rules
- Prefer imports from `app.domains.price_quotes.*` inside this domain.
- Cross-domain usage should call stable service APIs, not reach into route modules.

## Validation
- Covered by global backend gates: `ruff`, `mypy`, and `pytest apps/api/tests`.
