# Monitoring (Prometheus + Grafana) — Minimal Skeleton

This document describes the minimal monitoring scaffold added to the repository.

What was added
- `apps/api/app/infra/metrics.py`: helper to instrument the FastAPI app with Prometheus metrics and expose `/metrics`.

Quick start (local)
1. Install `prometheus_client` into your environment:

```powershell
. .venv\Scripts\Activate.ps1
pip install prometheus_client
```

2. Instrument the FastAPI app by calling `instrument_app(app)` in `apps/api/app/main.py` after app creation.

```python
from app.infra.metrics import instrument_app
instrument_app(app)
```

3. Start the app and open `http://localhost:8000/metrics`.

Prometheus scrape config (example)

```yaml
scrape_configs:
  - job_name: 'coffeestudio-backend'
    static_configs:
      - targets: ['host.docker.internal:8000']
```

Grafana
- Add Prometheus as a datasource and create dashboards on `http_requests_total` (method/path/status labels).

Notes
- The instrumentation helper is a safe no-op if `prometheus_client` is not installed.
- For production, add more metrics (latencies, DB pool stats, Celery task metrics) and configure secure access to `/metrics`.
