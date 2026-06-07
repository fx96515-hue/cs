"""Schemas for RAG AI Analyst functionality."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal


class ConversationMessage(BaseModel):
    """Single message in conversation history."""

    role: Literal["user", "assistant"]
    content: str


class RAGQuestion(BaseModel):
    """Question for the RAG AI Analyst."""

    question: str = Field(min_length=1, max_length=1000, description="User question")
    conversation_history: list[ConversationMessage] = Field(
        default=[],
        max_length=20,
        description="Previous conversation messages (max 20)",
    )


class RAGSource(BaseModel):
    """Source entity used in RAG response."""

    entity_type: str = Field(description="Type: 'cooperative' or 'roaster'")
    entity_id: int
    name: str
    similarity_score: float = Field(
        ge=0.0, le=1.0, description="Similarity score (0-1)"
    )


class RAGResponse(BaseModel):
    """Response from RAG AI Analyst."""

    answer: str = Field(description="AI-generated answer")
    sources: list[RAGSource] = Field(
        description="Source entities used to generate answer"
    )
    model: str = Field(description="LLM model used")
    tokens_used: int | None = Field(default=None, description="Tokens consumed")


class RAGStatusResponse(BaseModel):
    """Status of RAG service."""

    available: bool = Field(description="Whether RAG service is available")
    provider: str = Field(description="LLM provider name")
    model: str = Field(description="LLM model configured")
    embedding_provider: str = Field(description="Embedding provider name")
    embedding_model: str = Field(description="Embedding model configured")
