from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

from app.api.router import api_router
from app.core.config import settings
from app.infra.metrics import instrument_app
from app.core.logging import setup_logging
from app.core.error_handlers import (
    validation_exception_handler,
    http_exception_handler,
    integrity_error_handler,
    operational_error_handler,
    generic_exception_handler,
)
from app.middleware import InputValidationMiddleware, SecurityHeadersMiddleware

setup_logging()
log = structlog.get_logger(__name__)

app = FastAPI(title="CoffeeStudio API", version="0.1.0")

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter


# Custom rate limit handler
# Note: exc is typed as Exception for FastAPI compatibility but will be RateLimitExceeded
async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add comprehensive error handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(IntegrityError, integrity_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(OperationalError, operational_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, generic_exception_handler)

# Add security middleware
# Note: Middleware execution order matters in FastAPI
# Middleware added first executes last on the way out (response)
# Middleware added last executes first on the way in (request)
# So: InputValidation -> CORS -> Security Headers (on request)
#     Security Headers -> CORS -> InputValidation (on response)
app.add_middleware(SecurityHeadersMiddleware)  # Applied last to responses
app.add_middleware(InputValidationMiddleware)  # Applied first to requests

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "X-CSRF-Token",
        "X-Request-ID",
    ],
)

app.include_router(api_router)

# Additional Prometheus instrumentation helper (safe no-op if dependency missing)
try:
    instrument_app(app)
except Exception as exc:
    log.debug("prometheus_instrumentation_unavailable", exc_info=exc)

# Keep existing Instrumentator instrumentation if available
try:
    Instrumentator().instrument(app).expose(app)
except Exception as exc:
    log.debug("prometheus_instrumentator_unavailable", exc_info=exc)


# Startup event for auto-seeding
@app.on_event("startup")
async def startup_seed_data():
    """Seed default regions and demo data on startup if tables are empty."""
    from app.db.session import SessionLocal
    from app.services.peru_regions import seed_default_regions
    from app.services.seed_peru_regions import seed_peru_regions
    from app.services.seed_demo_data import seed_all_demo_data
    from sqlalchemy import inspect

    db = SessionLocal()
    try:
        log.info("startup_seed", status="starting")

        # Seed PeruRegion table (for regions API)
        peru_region_result = seed_default_regions(db)
        log.info("startup_seed_peru_regions", result=peru_region_result)

        # Seed Region table (for Peru Sourcing Intelligence)
        # Only if the table exists (it may not be in all deployments)
        inspector = inspect(db.get_bind())
        if "regions" in inspector.get_table_names():
            region_result = seed_peru_regions(db)
            log.info("startup_seed_regions", result=region_result)
        else:
            log.info(
                "startup_seed_regions",
                status="skipped",
                reason="regions table not found",
            )

        # Seed demo data (cooperatives, roasters, market observations)
        demo_result = seed_all_demo_data(db)
        log.info("startup_seed_demo", result=demo_result)

        log.info("startup_seed", status="completed")
    except Exception as e:
        log.error("startup_seed", error=str(e), exc_info=True)
    finally:
        db.close()
