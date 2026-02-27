"""Assistant Chat API endpoints (POST /assistant/chat, GET /assistant/status)."""

from __future__ import annotations

import structlog

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_db, require_auth
from app.core.config import settings
from app.schemas.assistant import AssistantStatusResponse, ChatRequest
from app.services.assistant import AssistantService

router = APIRouter()
log = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address)


@router.post("/chat")
@limiter.limit("20/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    db: Session = Depends(get_db),
    auth_info: dict = Depends(require_auth),
) -> StreamingResponse:
    """Stream a chat response from the RAG AI Assistant.

    Returns Server-Sent Events (SSE) stream with the following event types:

    - ``{"type": "session", "session_id": "..."}``           – first event
    - ``{"type": "chunk",   "content":    "..."}``           – token chunks
    - ``{"type": "done",    "sources": [...], "model": ""}`` – final event
    - ``{"type": "error",   "message":    "..."}``           – on failure

    Args:
        request: FastAPI request (for rate limiting)
        body: Chat request with message and optional session_id
        db: Database session
        auth_info: Authenticated user info

    Returns:
        StreamingResponse with ``text/event-stream`` media type

    Raises:
        HTTPException 503: If feature flag disabled or provider unavailable
    """
    if not settings.ASSISTANT_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Assistant Chat ist deaktiviert (Feature-Flag ASSISTANT_ENABLED=false).",
        )

    service = AssistantService()

    if not service.is_available():
        provider_info = service.get_provider_info()
        provider = provider_info["provider"]
        log.warning(
            "assistant_unavailable",
            provider=provider,
            user=auth_info.get("email"),
        )
        raise HTTPException(
            status_code=503,
            detail=_provider_error(provider),
        )

    log.info(
        "assistant_chat_request",
        user=auth_info.get("email"),
        session_id=body.session_id,
        message_length=len(body.message),
    )

    return StreamingResponse(
        service.stream_chat(
            message=body.message,
            session_id=body.session_id,
            db=db,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status", response_model=AssistantStatusResponse)
async def get_status(
    _: dict = Depends(require_auth),
) -> AssistantStatusResponse:
    """Return the status of the Assistant Chat service.

    Args:
        _: Authenticated user info

    Returns:
        Service availability and provider details
    """
    service = AssistantService()
    provider_info = service.get_provider_info()

    return AssistantStatusResponse(
        available=service.is_available(),
        enabled=settings.ASSISTANT_ENABLED,
        provider=provider_info["provider"],
        model=provider_info["model"],
    )


def _provider_error(provider: str) -> str:
    messages = {
        "ollama": (
            "Assistant nicht verfügbar. "
            "Starte Ollama: `ollama serve` und lade ein Modell: `ollama pull llama3.1:8b`"
        ),
        "openai": "Assistant nicht verfügbar. OPENAI_API_KEY ist nicht konfiguriert.",
        "groq": "Assistant nicht verfügbar. GROQ_API_KEY ist nicht konfiguriert.",
    }
    return messages.get(provider, "Assistant nicht verfügbar.")
