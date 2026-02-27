"""Schemas for the Assistant Chat endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for POST /assistant/chat."""

    message: str = Field(min_length=1, max_length=1000, description="User message")
    session_id: str | None = Field(
        default=None,
        description="Session ID for conversation history (omit to start new session)",
    )


class AssistantStatusResponse(BaseModel):
    """Status of the Assistant Chat service."""

    available: bool = Field(description="Whether the service is available")
    enabled: bool = Field(description="Whether the feature flag is enabled")
    provider: str = Field(description="LLM provider name")
    model: str = Field(description="LLM model configured")
