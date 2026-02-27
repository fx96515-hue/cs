"""RAG AI Analyst API endpoints."""

from __future__ import annotations

import structlog

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_db, require_auth
from app.core.config import settings
from app.schemas.rag_analyst import (
    RAGQuestion,
    RAGResponse,
    RAGStatusResponse,
)
from app.services.rag_analyst import RAGAnalystService

router = APIRouter()
log = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/ask", response_model=RAGResponse)
@limiter.limit("20/minute")
async def ask_analyst(
    request: Request,
    question: RAGQuestion,
    db: Session = Depends(get_db),
    auth_info: dict = Depends(require_auth),
):
    """Ask the RAG AI Analyst a question.

    Args:
        request: FastAPI request (for rate limiting)
        question: Question and conversation history
        db: Database session
        auth_info: Authenticated user info

    Returns:
        AI-generated answer with sources

    Raises:
        HTTPException: 503 if service unavailable, 500 on error
    """
    service = RAGAnalystService()

    # Check if service is available
    if not service.is_available():
        provider_info = service.get_provider_info()
        provider = provider_info["provider"]

        log.warning(
            "rag_analyst_unavailable",
            provider=provider,
            user=auth_info.get("email"),
        )

        # Provider-specific error messages
        if provider == "ollama":
            error_msg = (
                "RAG AI Analyst ist nicht verfügbar. "
                "Ollama ist nicht gestartet. "
                "Starte Ollama mit: `ollama serve` und lade ein Modell: `ollama pull llama3.1:8b`"
            )
        elif provider == "openai":
            error_msg = (
                "RAG AI Analyst ist nicht verfügbar. "
                "OPENAI_API_KEY ist nicht konfiguriert."
            )
        elif provider == "groq":
            error_msg = (
                "RAG AI Analyst ist nicht verfügbar. "
                "GROQ_API_KEY ist nicht konfiguriert."
            )
        else:
            error_msg = "RAG AI Analyst ist nicht verfügbar."

        raise HTTPException(
            status_code=503,
            detail=error_msg,
        )

    # Validate conversation history length
    if len(question.conversation_history) > settings.RAG_MAX_CONVERSATION_HISTORY:
        raise HTTPException(
            status_code=400,
            detail=f"Conversation history too long. Max {settings.RAG_MAX_CONVERSATION_HISTORY} messages.",
        )

    try:
        response = await service.ask(
            question=question.question,
            conversation_history=question.conversation_history,
            db=db,
        )

        log.info(
            "rag_analyst_question_answered",
            user=auth_info.get("email"),
            question_length=len(question.question),
            answer_length=len(response.answer),
            sources_count=len(response.sources),
        )

        return response

    except Exception as e:
        log.error(
            "rag_analyst_error",
            error=str(e),
            user=auth_info.get("email"),
        )
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Generieren der Antwort. Bitte versuchen Sie es erneut.",
        )


@router.get("/status", response_model=RAGStatusResponse)
async def get_status(
    _: dict = Depends(require_auth),
):
    """Get status of RAG AI Analyst service.

    Args:
        _: Authenticated user info

    Returns:
        Service status information with provider details
    """
    service = RAGAnalystService()
    provider_info = service.get_provider_info()

    return RAGStatusResponse(
        available=service.is_available(),
        provider=provider_info["provider"],
        model=provider_info["model"],
        embedding_provider=settings.RAG_EMBEDDING_PROVIDER,
        embedding_model=settings.RAG_EMBEDDING_MODEL,
    )
