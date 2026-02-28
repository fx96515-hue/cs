import logging
from typing import Any

try:
    from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
    from starlette.responses import Response
except Exception as exc:
    # prometheus_client or FastAPI not installed; provide no-op
    logging.getLogger(__name__).debug(
        "prometheus_instrumentation_unavailable", exc_info=exc
    )

    def instrument_app(app: Any) -> None:
        return
else:
    REQUEST_COUNTER = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )

    def instrument_app(app: Any) -> None:
        """Add a Prometheus /metrics endpoint and a simple request counter middleware.

        Safe to call even if prometheus_client is not available in the environment
        (function becomes a no-op in that case).
        """

        @app.middleware("http")
        async def _metrics_middleware(request, call_next):
            response = await call_next(request)
            try:
                REQUEST_COUNTER.labels(
                    request.method, request.url.path, str(response.status_code)
                ).inc()
            except Exception as exc:
                logging.getLogger(__name__).debug(
                    "prometheus_metrics_increment_failed", exc_info=exc
                )
            return response

        @app.get("/metrics")
        def _metrics():
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
