"""AI-powered test failure analyzer."""

from typing import Any
import json
import os
import logging
from dataclasses import dataclass

try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)


@dataclass
class TestFailure:
    """Represents a test failure with all relevant information."""

    test_name: str
    error_type: str
    error_message: str
    stack_trace: str
    file_path: str
    line_number: int
    test_code: str
    source_code: str


class AIFailureAnalyzer:
    """Analyzes test failures using AI and suggests fixes."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """Initialize the AI failure analyzer.

        Args:
            api_key: OpenAI API key. If not provided, will try to get from environment.
            model: OpenAI model to use for analysis. If not provided, uses QA_AI_MODEL env var or 'gpt-4'.
        """
        if openai is None:
            raise ImportError(
                "openai package is required for AIFailureAnalyzer. "
                "Install it with: pip install openai"
            )

        api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("QA_AI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY or QA_AI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = openai.OpenAI(api_key=api_key)
        self.model = model or os.getenv("QA_AI_MODEL", "gpt-4")

    def analyze_failure(self, failure: TestFailure) -> dict[str, Any]:
        """Analyze a test failure and generate fix suggestion.

        Args:
            failure: TestFailure object containing failure details.

        Returns:
            Dictionary containing:
                - root_cause: str - What exactly is broken
                - severity: 'low' | 'medium' | 'high' | 'critical'
                - fix_suggestions: List[str] - Step-by-step fix instructions
                - code_fix: str - Actual code to apply
                - confidence: float - 0-100% confidence in the fix
                - similar_issues: List[str] - Related bugs to check
                - prevention_tips: List[str] - How to avoid this in future
        """
        prompt = self._build_analysis_prompt(failure)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,  # Low temperature for precise code analysis
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("AI response content is None")

        return json.loads(content)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI analyzer."""
        return """You are an expert Python/TypeScript engineer specializing in:
- FastAPI backend debugging
- SQLAlchemy ORM issues
- Pytest test failures
- React/Next.js frontend bugs

Analyze test failures and provide:
1. Root cause analysis
2. Severity assessment
3. Concrete fix suggestions with code
4. Prevention strategies

Always return valid JSON with the specified structure."""

    def _build_analysis_prompt(self, failure: TestFailure) -> str:
        """Build the analysis prompt for the AI."""
        return f"""
# Test Failure Analysis Request

## Failed Test
**Test Name:** {failure.test_name}
**File:** {failure.file_path}:{failure.line_number}

## Error Details
**Type:** {failure.error_type}
**Message:** {failure.error_message}

## Stack Trace
```
{failure.stack_trace}
```

## Test Code
```python
{failure.test_code}
```

## Source Code (under test)
```python
{failure.source_code}
```

## Your Task
Analyze this failure and provide:
1. **Root cause** - What exactly is broken?
2. **Severity** - How critical is this bug? (low/medium/high/critical)
3. **Fix suggestions** - Step-by-step how to fix (list of strings)
4. **Code fix** - Actual code patch to apply (complete fixed code)
5. **Confidence** - How sure are you (0-100)?
6. **Similar issues** - Related bugs to check (list of strings)
7. **Prevention tips** - How to avoid this in future (list of strings)

Return as JSON with these exact keys: root_cause, severity, fix_suggestions, code_fix, confidence, similar_issues, prevention_tips
"""
