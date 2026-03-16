# Enterprise Baseline Audit (2026-03-15)

## Scope

Repository: `CoffeeStudio`  
Branch: `audit/enterprise-baseline-20260315`

This baseline captures the current technical status before broader hardening/refactoring work.

## Verified Gates

- `docker compose config -q`: PASS
- `docker compose -f docker-compose.stack.yml config -q`: PASS
- `apps/api`: `pytest -q`: PASS (`708 passed, 3 skipped`)
- `apps/api`: `ruff check app tests`: PASS
- `apps/api`: `mypy --config-file ../../mypy.ini app`: PASS
- `apps/web`: `npm run lint`: PASS
- `apps/web`: `npx tsc --noEmit`: PASS
- `apps/web`: `npm run build`: PASS
- `apps/web`: `npm audit --omit=dev --audit-level=high`: PASS (`0 vulnerabilities`)
- `apps/api`: `python -m pip check`: PASS
- `docker compose up -d --build`: PASS
- `powershell -File scripts/win/smoke.ps1`: PASS

## Critical Findings (Phase 3 priority)

1. Broken integration smoke script (`scripts/integration_smoke_test.sh`)
- Status: FIXED
- Issue: merge-damaged structure (duplicate functions, malformed flow).
- Action: rebuilt script with deterministic phases, counters, auth flow, and clear failure handling.

2. Windows smoke auth false-negative
- Status: FIXED
- Issue: calls used non-canonical endpoints (`/cooperatives`, `/roasters`) and could lose bearer headers on redirect.
- Action: switched to canonical routes with trailing slash and fixed token-length output formatting.

3. Frontend Docker image critical CVE (zlib)
- Status: FIXED
- Issue: `coffeestudio-frontend:local` reported `CVE-2026-22184` (CRITICAL, fixed version available).
- Action: upgraded `zlib` in frontend Docker base stage (`apk upgrade --no-cache zlib`) and re-scanned.
- Validation: Trivy HIGH/CRITICAL result is now clean for frontend image.

4. Insecure local defaults and broad local port exposure in compose/scripts
- Status: FIXED
- Issue: permissive defaults (`adminadmin`, weak JWT fallback) and non-loopback published ports increased local attack surface.
- Action: hardened compose and Windows scripts:
  - bind published dev ports to loopback (`127.0.0.1`)
  - require `JWT_SECRET` in compose runtime
  - require explicit admin passwords for Grafana/Keycloak stack services
  - generate strong local secrets automatically in `run_windows.ps1`
  - removed implicit `adminadmin` fallback in setup scripts

5. Auth email matching could fail on mixed-case input
- Status: FIXED
- Issue: login/bootstrap user lookup compared emails case-sensitively.
- Action: normalized email lookup to case-insensitive query paths and added regression coverage.

6. Dev bootstrap endpoint reachable from non-local clients in dev/test
- Status: FIXED
- Issue: `/auth/dev/bootstrap` had no client-origin boundary beyond environment gating.
- Action: enforced loopback-only access and added tests for local/remote host detection.

7. Circuit reset endpoint accepted unbounded provider keys and returned 200 on unknown provider
- Status: FIXED
- Issue: `/data-health/reset-circuit/{provider}` accepted broad input and mixed errors into success responses.
- Action: enforced bounded provider key validation and returned proper `404` for unknown providers.

8. Pipeline trigger endpoint accepted broad source-name input
- Status: FIXED
- Issue: `/pipeline/trigger/{source_name}` accepted broad arbitrary path values.
- Action: added bounded/pattern-validated path input and canonical alias mapping for supported trigger sources.

9. Scheduler trigger/status endpoints accepted unbounded identifiers
- Status: FIXED
- Issue: `/scheduler/jobs/{job_id}/run` and `/scheduler/tasks/{task_id}` lacked explicit identifier bounds.
- Action: added bounded/pattern-validated path parameters and expanded scheduler route test coverage.

10. Freshness monitor returned placeholder source metadata
- Status: FIXED
- Issue: market freshness observations returned `source: None` even when `source_id` was present.
- Action: implemented source-name resolution with lightweight caching and added dedicated monitor tests.

11. Source CRUD accepted weak kind/reliability inputs
- Status: FIXED
- Issue: source schema accepted unconstrained `kind` values and out-of-range reliability scores.
- Action: constrained/normalized allowed source kinds, bounded reliability to `0..1`, and enforced `source_id >= 1` at route boundaries.

12. Legacy UI token usage (`var(--muted)`) had no guaranteed root definition
- Status: FIXED
- Issue: several pages/components still referenced `--muted` despite primary token migration to `--color-text-muted`.
- Action: added `--muted` alias in global design tokens for backward-compatible consistency.

13. Core entity routes accepted non-positive path IDs
- Status: FIXED
- Issue: cooperative/roaster/report/peru entity routes accepted unbounded integer IDs in path parameters.
- Action: enforced `Path(ge=1)` across those route boundaries and added dedicated negative-path tests.

14. Outreach request schema accepted weak variants
- Status: FIXED
- Issue: outreach input fields (`entity_type`, `language`, `purpose`, `entity_id`) were not strictly constrained.
- Action: switched to strict typed request schema (`Literal` + positive integer constraint) and extended API tests.

15. Peru region refresh/intelligence inputs lacked explicit bounds
- Status: FIXED
- Issue: `region_name` input accepted weak/blank variants across refresh/intelligence routes.
- Action: added schema/path boundaries and normalization-compatible validation with regression tests.

16. Discovery task status exposed raw failure text and accepted broad task IDs
- Status: FIXED
- Issue: `/discovery/seed/{task_id}` leaked raw task failure details and allowed unconstrained ids.
- Action: sanitized failure payloads and enforced bounded/pattern-validated task IDs; added route tests.

17. Discovery seed accepted weak country filter values
- Status: FIXED
- Issue: `country_filter` was optional but unvalidated free text.
- Action: enforced ISO-2 validation and normalization (uppercase) with test coverage.

18. Peru region detail page used ad-hoc error-state rendering
- Status: IMPROVED
- Issue: error state used custom inline styling instead of shared alert semantics.
- Action: aligned page-level error panel to shared `ErrorPanel` pattern while preserving current visual language.

19. Feature import template endpoint accepted broad path input and echoed unknown type
- Status: FIXED
- Issue: `/features/import-template/{data_type}` accepted unconstrained path values and returned user input in 404 detail.
- Action: bounded/pattern-validated `data_type` path parameter and sanitized not-found detail.

20. Auto-outreach accepted weak campaign and status query/path inputs
- Status: FIXED
- Issue: campaign input and status/suggestions endpoints lacked strict bounds on names, scores, ids, and limits.
- Action: tightened schema/path/query validation (`name`, score ranges, `entity_id >= 1`, bounded `limit`) and added API regression tests.

21. Peru sourcing endpoints returned detailed not-found messages
- Status: FIXED
- Issue: some peru sourcing 404 responses echoed user-provided identifiers.
- Action: standardized not-found details to generic `Not found` for safer and more consistent error contracts.

22. Regions filter endpoint accepted weak free-text country input
- Status: FIXED
- Issue: `/regions` accepted unconstrained `country` query values.
- Action: added bounded/pattern validation and normalization for country filter values with regression tests.

23. ML training endpoint exposed raw error detail
- Status: FIXED
- Issue: `/ml/train/train/{model_type}` could return internal exception text to clients.
- Action: sanitized ValueError/runtime error responses to stable generic messages and added dedicated API tests.

13. Core entity routes accepted non-positive path IDs
- Status: FIXED
- Issue: several cooperative/roaster/report/peru routes accepted unbounded integer IDs in path parameters.
- Action: enforced `Path(ge=1)` boundaries and added regression tests for invalid zero IDs.

14. Outreach endpoint accepted weak request variants
- Status: FIXED
- Issue: outreach request accepted unconstrained string fields for entity/language/purpose.
- Action: enforced strict typed schema (`Literal`-based) + positive `entity_id` and counterpart-name validation.

24. Knowledge-graph routes leaked internal not-found details
- Status: FIXED
- Issue: multiple graph endpoints returned raw `ValueError` text in 404 responses.
- Action: standardized not-found details to generic `Not found` across graph analysis/path/connections endpoints and hardened API expectation tests.

25. Dedup/outreach endpoints exposed raw service validation text on 400
- Status: FIXED
- Issue: `dedup` and `outreach` routes surfaced raw `ValueError` details to clients.
- Action: standardized both routes to stable `Invalid request` responses and added regression assertions for the API error contract.

26. Frontend page-header structure drift across analytics/search/report pages
- Status: IMPROVED
- Issue: several pages used `div.pageHeader`/`pageActions` instead of the shared semantic header structure.
- Action: aligned `ml`, `reports`, `search`, and `sentiment` pages to `header.pageHeader` + `pageHeaderContent/pageHeaderActions` for consistent layout semantics.

27. Docker build contexts still included avoidable local/developer files
- Status: IMPROVED
- Issue: per-app Docker contexts included test/docs/log artifacts not required for runtime image builds.
- Action: tightened `apps/api/.dockerignore` and `apps/web/.dockerignore` to exclude tests, local logs, docs, and auxiliary dev files; verified compose configuration remains valid.

28. ML data import endpoints leaked internal exception text on failure
- Status: FIXED
- Issue: `/ml/data/import-freight` and `/ml/data/import-prices` returned raw exception details in 400 responses.
- Action: standardized both endpoints to generic `Import failed` and added regression tests that assert sanitized error contracts.

29. Dev bootstrap endpoint exposed configuration-validation internals
- Status: FIXED
- Issue: `/auth/dev/bootstrap` returned raw password/email validation details.
- Action: replaced response details with stable generic contract messages and added tests for sanitized password/email-config failures.

30. ML batch predictions leaked internal per-item errors and accepted weak route/query boundaries
- Status: FIXED
- Issue: batch endpoints returned raw exception messages in `errors[]`; selected ML route/query inputs lacked explicit bounds.
- Action: standardized batch item errors to `Prediction failed`, bounded `months_back` (`1..120`) and constrained `task_id` format/length with regression tests.

31. Frontend page-header consistency gaps remained on detail/intelligence pages
- Status: IMPROVED
- Issue: several detail and intelligence pages still used legacy `div.pageHeader` structures.
- Action: aligned `news`, `graph`, `cooperatives/[id]`, `roasters/[id]`, and `peru-sourcing/regions/[name]` to shared `header.pageHeader` semantics and header action containers.

32. ML model detail routes accepted non-positive model IDs
- Status: FIXED
- Issue: ML model detail/retrain/feature-importance routes lacked explicit positive ID bounds.
- Action: enforced `model_id >= 1` path validation and added regression tests for rejected zero IDs.

33. Market websocket auth rejection reasons exposed unnecessary detail variants
- Status: FIXED
- Issue: websocket auth could return different rejection reason strings (`Missing token`, role/account hints).
- Action: standardized auth-related websocket close reasons to `Unauthorized` and added route-level regression tests for sanitized helper behavior.

34. Lots endpoints accepted non-positive identifiers in path/query boundaries
- Status: FIXED
- Issue: lots detail/mutation routes and cooperative filter accepted non-positive IDs.
- Action: enforced positive bounds (`Path(ge=1)`, `Query(ge=1)`) and added regression tests for rejected zero values.

35. Deals endpoints accepted non-positive identifiers in path/query boundaries
- Status: FIXED
- Issue: deals detail/mutation routes and list filters accepted non-positive IDs.
- Action: enforced positive bounds (`Path(ge=1)`, `Query(ge=1)`) and added dedicated API boundary tests.

## High-Priority Findings

1. Local security scan noise / temporary artifacts
- Status: IMPROVED
- Action: ignore rule added for local temp dumps (`.tmp_*.json`) to improve repo hygiene.

2. Frontend lint quality warning in report detail page
- Status: FIXED
- Action: removed synchronous `setState` call from `useEffect` path.

3. Frontend detail/dashboard layout inconsistencies across pages
- Status: PARTIAL
- Action: standardized shared `content` container usage and unified detail page wrappers/alerts on high-traffic pages.
- Remaining exception: `apps/web/app/analyst/page.tsx` keeps dedicated `chatLayout` by design.

## Medium Findings

1. Formatting drift in backend codebase (`ruff format --check` reports many files)
- Status: OPEN
- Note: CI currently formats first and then checks; this does not block CI but indicates style drift.

2. KI chat page had non-standard root wrapper
- Status: FIXED
- Action: aligned to shared `content` wrapper while preserving full-height chat behavior.

## Commits Created in This Audit Slice

- `5e136f6` `fix(smoke): restore integration script and clear frontend lint warning`
- `ce272a8` `fix(smoke-win): avoid auth header loss on redirected endpoints`
- `1fe0eae` `docs(audit): add enterprise baseline status and priorities`
- `43c6e60` `fix(smoke-win): silence expected health probe curl noise`
- `f6051db` `harden(docker): patch frontend image zlib critical CVE`
- `13de8f4` `harden(local): enforce secure compose defaults and bootstrap secrets`
- `fd40d1e` `improve(frontend): align lot detail page with shared dashboard patterns`
- `557c055` `improve(frontend): unify detail-page wrapper and success alert classes`
- `c0606fa` `improve(frontend): standardize page content wrapper on key dashboards`
- `acf2309` `improve(frontend): align content container usage across operations pages`
- `b717d88` `improve(frontend): apply shared content layout to additional workflow pages`
- `3ea950a` `chore(repo): remove stale pre-commit backup config`
- `d8cbe8e` `improve(frontend): align KI page wrapper with shared content layout`
- `22f5a18` `docs(audit): update baseline with current hardening progress`
- `2b5ea9d` `harden(auth): normalize email matching for login and bootstrap`
- `cc88614` `chore(repo): remove stale QA backup file`
- `c2b7db7` `docs(audit): record auth hardening and latest validation`
- `25ab7d4` `chore(repo): deduplicate and normalize gitignore rules`
- `55d3469` `harden(auth): restrict dev bootstrap endpoint to loopback clients`
- `15cc237` `harden(api): enforce provider validation on circuit reset endpoint`
- `4739d32` `docs(audit): record circuit-reset validation hardening`
- `b162e47` `harden(api): validate pipeline trigger source names and aliases`
- `ea88345` `harden(api): validate scheduler job/task identifiers`
- `d48bcb2` `docs(audit): record scheduler identifier hardening`
- `c6a9ed8` `improve(data): resolve freshness source names and cover with tests`
- `2eeeb2c` `docs(audit): capture freshness source metadata improvement`
- `07b759e` `harden(api): tighten source schema and route id validation`
- `2c9ad75` `docs(audit): record source schema and route-boundary hardening`
- `f561a23` `improve(ui): add muted token alias for legacy component consistency`
- `cfef249` `docs(audit): capture pipeline trigger validation hardening`
- `c2b6c18` `chore(docker): exclude local QA and diagnostics artifacts from build context`
- `fa03e5f` `docs(audit): record route-id and outreach validation hardening`
- `4bd7d28` `harden(api): validate peru region inputs for refresh and intelligence routes`
- `aa0345e` `harden(api): validate discovery task ids and sanitize failure payloads`
- `be0ed9b` `harden(api): validate and normalize discovery country filters`
- `b4e2fb3` `docs(audit): sync baseline with latest boundary and error-hardening slices`
- `7c55a7b` `improve(frontend): align peru region error state with shared alert pattern`
- `efc65ab` `docs(audit): log discovery hardening and peru region UI consistency update`
- `86ccfd6` `harden(api): constrain feature template path input and sanitize 404 detail`
- `a23e733` `docs(audit): record discovery/features hardening progress and latest test baseline`
- `689ce9a` `harden(api): tighten auto-outreach request and path/query validation`
- `f477447` `docs(audit): capture auto-outreach validation hardening and latest baseline`
- `b932f06` `harden(api): sanitize peru sourcing not-found error details`
- `2449bab` `docs(audit): log peru sourcing error-contract hardening`
- `f7cae09` `harden(api): validate regions country filter input`
- `8cddddd` `docs(audit): record regions country-filter validation hardening`
- `7cda909` `harden(api): sanitize ml training error details`
- `eba7a00` `docs(audit): capture muted-token compatibility hardening`
- `a8a4949` `harden(api): enforce positive path ids across core entity routes`
- `a78d3cf` `harden(api): enforce strict outreach request schema validation`
- `dbe5e19` `harden(api): sanitize knowledge-graph not-found error details`
- `17d37a6` `docs(audit): record knowledge-graph error-contract hardening`
- `212b7a8` `harden(api): standardize dedup and outreach bad-request details`
- `d395aaf` `docs(audit): capture dedup/outreach error-contract hardening`
- `a1d747a` `improve(frontend): unify page-header structure across analytics pages`
- `6bcddda` `docs(audit): log frontend header consistency slice`
- `a367a25` `chore(docker): tighten app build contexts via dockerignore`
- `4a72714` `docs(audit): record docker context cleanup slice`
- `6ab7299` `harden(api): sanitize ml import failure error details`
- `c378bf2` `docs(audit): record ml import hardening and gate updates`
- `361c158` `harden(auth): sanitize bootstrap config validation error details`
- `9bbf50b` `docs(audit): log bootstrap error-contract hardening`
- `c4e297d` `harden(api): constrain ml task/trend params and sanitize batch errors`
- `6447ce4` `docs(audit): capture ml boundary and batch-error hardening`
- `d5c74db` `improve(frontend): align detail and intelligence pages to shared header pattern`
- `6c2aae5` `docs(audit): record additional frontend header harmonization`
- `18bde8f` `harden(api): enforce positive ml model ids on model routes`
- `cd884bc` `docs(audit): record ml model-id boundary hardening`
- `f0fb942` `harden(api): sanitize market websocket auth rejection reasons`
- `e9dcf6f` `docs(audit): capture websocket auth-contract hardening`
- `0458b6e` `harden(api): enforce positive lot ids and cooperative filter bounds`
- `e4ba9d0` `docs(dev): align local frontend setup to npm workflow`
- `94bba5b` `docs(audit): finalize latest gate results and lot-boundary hardening`
- `58fc382` `harden(api): enforce positive deal ids and filter bounds`

## Next Execution Slice

1. Continue targeted backend boundary hardening on remaining mutation/list routes with unconstrained IDs.
2. Keep frontend consistency improvements focused on shared interaction/state patterns (without redesign).
3. Repeat full-gate validation after each hardening slice and keep this baseline synchronized.
