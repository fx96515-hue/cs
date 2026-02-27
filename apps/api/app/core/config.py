from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import logging


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required settings that must come from environment
    DATABASE_URL: str = Field(default="", min_length=1)
    REDIS_URL: str = Field(default="", min_length=1)
    JWT_SECRET: str = Field(default="", min_length=32)
    JWT_ISSUER: str = "coffeestudio"
    JWT_AUDIENCE: str = "coffeestudio-web"
    CORS_ORIGINS: str = "http://localhost:3000"
    TZ: str = "Europe/Berlin"

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret_strength(cls, v: str) -> str:
        """Validate JWT secret strength for production security."""
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters for security. "
                "Generate a strong secret: openssl rand -hex 16"
            )
        if len(v) < 64:
            logger = logging.getLogger(__name__)
            logger.warning(
                "JWT_SECRET is less than 64 characters. "
                "For production, use at least 64 characters: openssl rand -hex 32"
            )
        return v

    # Dev bootstrap (only used by /auth/dev/bootstrap)
    # Must be a *valid* email (no .local/.test special-use).
    BOOTSTRAP_ADMIN_EMAIL: str = "admin@coffeestudio.com"
    # Intentionally no baked-in default password (fail-fast if missing).
    BOOTSTRAP_ADMIN_PASSWORD: str | None = None

    # --- Perplexity (Sonar) API ---
    # Docs: https://docs.perplexity.ai/
    PERPLEXITY_API_KEY: str | None = None
    PERPLEXITY_BASE_URL: str = "https://api.perplexity.ai"
    # For discovery tasks we prefer models with web/search + structured outputs
    PERPLEXITY_MODEL_DISCOVERY: str = "sonar-pro"
    PERPLEXITY_TIMEOUT_SECONDS: int = 60

    # --- Enrichment HTTP allowlists (SSRF protection) ---
    # Comma-separated hostnames and/or domain suffixes for fetch_text().
    # Example hosts: "www.example.com,api.example.org"
    # Example domains: ".example.com,.example.org"
    ENRICH_ALLOWED_HOSTS: str = ""
    ENRICH_ALLOWED_DOMAINS: str = ""

    # --- Data freshness defaults (days) ---
    KOOPS_STALE_DAYS: int = 60
    ROESTER_STALE_DAYS: int = 90
    NEWS_STALE_DAYS: int = 2
    FX_STALE_DAYS: int = 2

    # --- Scheduled refresh times (Europe/Berlin) ---
    # Format: "HH:MM,HH:MM,HH:MM"
    NEWS_REFRESH_TIMES: str = "07:30,14:00,20:00"
    MARKET_REFRESH_TIMES: str = "07:30,14:00,20:00"

    # Data Pipeline settings
    DATA_PIPELINE_CIRCUIT_BREAKER_THRESHOLD: int = 3
    DATA_PIPELINE_CIRCUIT_BREAKER_TIMEOUT_S: int = 300
    DATA_PIPELINE_MAX_RETRIES: int = 3

    # Intelligence refresh schedule
    INTELLIGENCE_REFRESH_TIMES: str = "06:00,12:00,18:00,00:00"
    AUTO_ENRICH_TIME: str = "03:00"
    # Daily embedding backfill schedule (HH:MM, Europe/Berlin)
    EMBEDDINGS_TIME: str = "04:00"

    # --- Feature flags ---
    # Set SEMANTIC_SEARCH_ENABLED=false to disable all /search/* endpoints.
    SEMANTIC_SEARCH_ENABLED: bool = True
    # Set ASSISTANT_ENABLED=false to disable all /assistant/* endpoints.
    ASSISTANT_ENABLED: bool = True
    # Set ANOMALY_DETECTION_ENABLED=false to disable anomaly detection scan and endpoints.
    ANOMALY_DETECTION_ENABLED: bool = True
    # Set GRAPH_ENABLED=false to disable knowledge graph features.
    GRAPH_ENABLED: bool = True
    # Set SENTIMENT_ENABLED=false to disable sentiment analysis features.
    SENTIMENT_ENABLED: bool = True
    # Set REALTIME_PRICE_FEED_ENABLED=false to disable real-time price feeds.
    REALTIME_PRICE_FEED_ENABLED: bool = True
    # Set EMBEDDING_TASKS_ENABLED=false to skip background embedding updates.
    EMBEDDING_TASKS_ENABLED: bool = True

    # --- Anomaly Detection ---
    # Daily anomaly scan schedule (HH:MM, Europe/Berlin)
    ANOMALY_SCAN_TIME: str = "02:00"

    # --- Assistant Chat (RAG Streaming) ---
    ASSISTANT_SESSION_TTL_SECONDS: int = 86400  # 24 hours

    # --- OpenAI for semantic search embeddings (kept for optional use) ---
    OPENAI_API_KEY: str | None = None

    # --- Local / sentence-transformers embeddings (default provider) ---
    # EMBEDDING_PROVIDER selects the backend used for pgvector embedding generation.
    # "local" uses sentence-transformers (CPU-only, no API key required).
    # "openai" falls back to the OpenAI API (requires OPENAI_API_KEY).
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Optional filesystem cache directory for the sentence-transformers model.
    # Defaults to the HuggingFace cache (~/.cache/huggingface/hub) when unset.
    SENTENCE_TRANSFORMERS_CACHE: str | None = None

    # --- RAG AI Analyst (Multi-Provider) ---
    RAG_PROVIDER: str = "ollama"  # ollama | openai | groq
    RAG_LLM_MODEL: str = "llama3.1:8b"  # Provider-specific model
    RAG_EMBEDDING_PROVIDER: str = "openai"  # Separate from LLM provider
    RAG_EMBEDDING_MODEL: str = (
        "text-embedding-3-small"  # Or "nomic-embed-text" for Ollama
    )
    RAG_MAX_CONTEXT_ENTITIES: int = 10
    RAG_MAX_CONVERSATION_HISTORY: int = 20
    RAG_TEMPERATURE: float = 0.3

    # --- Ollama (local LLM server) ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # --- Groq (optional cloud provider) ---
    GROQ_API_KEY: str | None = None

    # --- Machine Learning ---
    # Model type to use for training: "random_forest" or "xgboost"
    # RandomForest is retained as fallback; set to "xgboost" to use XGBoost.
    ML_MODEL_TYPE: str = "random_forest"

    def cors_origins_list(self) -> List[str]:
        return [s.strip() for s in self.CORS_ORIGINS.split(",") if s.strip()]

    def refresh_times_list(self, raw: str) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        for part in (raw or "").split(","):
            part = part.strip()
            if not part:
                continue
            hh, mm = part.split(":")
            out.append((int(hh), int(mm)))
        return out


settings = Settings()
