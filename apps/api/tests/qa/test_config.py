"""Tests for QA system configuration."""

from app.qa.config import QAConfig


def test_qa_config_defaults():
    """Test QA configuration default values."""
    config = QAConfig(ai_api_key="test_key")

    assert config.ai_provider == "openai"
    assert config.ai_model == "gpt-4-turbo-preview"
    assert config.ai_api_key == "test_key"
    assert config.auto_fix_enabled is False
    assert config.confidence_threshold == 85.0
    assert config.max_fixes_per_run == 5
    assert config.analyze_stack_depth == 10
    assert config.include_git_history is True
    assert config.notify_on_failure is True
    assert config.notification_webhook is None


def test_qa_config_custom_values():
    """Test QA configuration with custom values."""
    config = QAConfig(
        ai_api_key="custom_key",
        ai_model="gpt-4",
        auto_fix_enabled=True,
        confidence_threshold=90.0,
        max_fixes_per_run=10,
    )

    assert config.ai_api_key == "custom_key"
    assert config.ai_model == "gpt-4"
    assert config.auto_fix_enabled is True
    assert config.confidence_threshold == 90.0
    assert config.max_fixes_per_run == 10
