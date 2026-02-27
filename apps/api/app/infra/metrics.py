try:
    from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
    from fastapi import FastAPI
    from starlette.responses import Response
except Exception:
    # prometheus_client or FastAPI not installed; provide no-op
    def instrument_app(app):
        return
else:
    REQUEST_COUNTER = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status"],
    )

    def instrument_app(app: FastAPI):
        """Add a Prometheus /metrics endpoint and a simple request counter middleware.

        Safe to call even if prometheus_client is not available in the environment
        (function becomes a no-op in that case).
        """

        @app.middleware("http")
        async def _metrics_middleware(request, call_next):
            response = await call_next(request)
            try:
                REQUEST_COUNTER.labels(request.method, request.url.path, str(response.status_code)).inc()
            except Exception:
                pass
            return response

        @app.get("/metrics")
        def _metrics():
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
