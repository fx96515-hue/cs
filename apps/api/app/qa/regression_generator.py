"""Regression test generator for fixed bugs."""

import os

try:
    import openai
except ImportError:
    openai = None


class RegressionTestGenerator:
    """Generates regression tests for fixed bugs."""

    def __init__(
        self, ai_client: "openai.OpenAI | None" = None, api_key: str | None = None
    ):
        """Initialize the regression test generator.

        Args:
            ai_client: OpenAI client instance. If not provided, will create one.
            api_key: OpenAI API key. If not provided, will try to get from environment.
        """
        if openai is None:
            raise ImportError(
                "openai package is required for RegressionTestGenerator. "
                "Install it with: pip install openai"
            )

        if ai_client is None:
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                    "or pass api_key parameter."
                )
            self.ai = openai.OpenAI(api_key=api_key)
        else:
            self.ai = ai_client

    def generate_regression_test(
        self, bug_description: str, fixed_code: str, test_framework: str = "pytest"
    ) -> str:
        """Generate a regression test for a fixed bug.

        Args:
            bug_description: Description of the bug that was fixed.
            fixed_code: The code after the fix was applied.
            test_framework: Test framework to use (default: pytest).

        Returns:
            Complete test code ready to add to test suite.
        """
        prompt = f"""
Generate a comprehensive regression test for this bug fix:

## Bug Description
{bug_description}

## Fixed Code
```python
{fixed_code}
```

## Requirements
- Framework: {test_framework}
- Test must verify the bug is fixed
- Test must fail if bug reoccurs
- Include edge cases
- Use proper fixtures if needed
- Add clear docstring
- Follow pytest conventions

Generate COMPLETE test code, not a stub.
Return ONLY the test code, no explanations.
"""

        response = self.ai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert test engineer. Generate complete, "
                        "production-ready test code. Return only the test code, "
                        "no markdown formatting or explanations."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        test_code = response.choices[0].message.content

        if test_code is None:
            raise ValueError("AI response content is None")

        # Clean up markdown code blocks if present
        if test_code.startswith("```"):
            lines = test_code.split("\n")
            # Remove first and last line if they are code block markers
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            test_code = "\n".join(lines)

        return test_code
