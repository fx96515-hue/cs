"""Configuration for AI-powered QA system."""

from pydantic_settings import BaseSettings


class QAConfig(BaseSettings):
    """Configuration for AI-powered QA system."""

    # AI Provider
    ai_provider: str = "openai"  # openai | anthropic | azure
    ai_model: str = "gpt-4-turbo-preview"
    ai_api_key: str = ""

    # Auto-fix settings
    auto_fix_enabled: bool = False
    confidence_threshold: float = 85.0  # Min confidence for auto-fix
    max_fixes_per_run: int = 5

    # Analysis settings
    analyze_stack_depth: int = 10  # Lines of stack trace to analyze
    include_git_history: bool = True  # Include recent commits in analysis

    # Notification settings
    notify_on_failure: bool = True
    notification_webhook: str | None = None

    class Config:
        env_file = ".env"
        env_prefix = "QA_"
