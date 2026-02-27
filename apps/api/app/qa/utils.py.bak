"""Utilities for parsing test output and extracting failure information."""

import re
import json
import logging
from pathlib import Path
from typing import Any

from .failure_analyzer import TestFailure

logger = logging.getLogger(__name__)


def parse_pytest_output(output: str) -> list[TestFailure]:
    """Parse pytest output and extract test failures.

    Args:
        output: Raw pytest output text.

    Returns:
        List of TestFailure objects.
    """
    failures = []

    # Split output into sections
    sections = output.split("FAILED ")

    for section in sections[1:]:  # Skip the first section (before first FAILED)
        try:
            failure = _parse_failure_section(section)
            if failure:
                failures.append(failure)
        except Exception as e:
            logger.warning(f"Failed to parse failure section: {e}")
            continue

    return failures


def _parse_failure_section(section: str) -> TestFailure | None:
    """Parse a single failure section from pytest output.

    Args:
        section: Text section containing a single test failure.

    Returns:
        TestFailure object or None if parsing failed.
    """
    lines = section.split("\n")

    # First line contains test name
    test_line = lines[0]
    test_match = re.search(r"([^:]+)::([^ ]+)", test_line)
    if not test_match:
        return None

    file_path = test_match.group(1)
    test_name = test_match.group(2)

    # Extract error type and message
    error_type = "Unknown"
    error_message = ""
    stack_trace = []
    line_number = 0

    in_traceback = False
    for line in lines[1:]:
        # Look for error type (usually all caps or ends with Error/Exception)
        if re.match(r"^[A-Z][a-zA-Z]*(?:Error|Exception):", line):
            parts = line.split(":", 1)
            error_type = parts[0].strip()
            if len(parts) > 1:
                error_message = parts[1].strip()

        # Build stack trace
        if "Traceback" in line or in_traceback:
            in_traceback = True
            stack_trace.append(line)

        # Extract line number from traceback
        line_match = re.search(r"line (\d+)", line)
        if line_match and line_number == 0:
            line_number = int(line_match.group(1))

    # Try to read test code and source code
    test_code = _read_file_section(file_path, test_name)
    source_code = ""  # Would need more context to extract

    return TestFailure(
        test_name=test_name,
        error_type=error_type,
        error_message=error_message,
        stack_trace="\n".join(stack_trace),
        file_path=file_path,
        line_number=line_number or 1,
        test_code=test_code,
        source_code=source_code,
    )


def _read_file_section(file_path: str, function_name: str) -> str:
    """Read a specific function from a file.

    Args:
        file_path: Path to the file.
        function_name: Name of the function to extract.

    Returns:
        Function code as string.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return ""

        content = path.read_text()

        # Find the function definition
        pattern = rf"^(def {function_name}\([^)]*\):.*?)(?=^def |\Z)"
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

        if match:
            return match.group(1).strip()

        return ""
    except Exception:
        return ""


def parse_pytest_json_report(json_path: str) -> list[TestFailure]:
    """Parse pytest JSON report and extract test failures.

    Args:
        json_path: Path to pytest JSON report file.

    Returns:
        List of TestFailure objects.
    """
    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        failures = []

        for test in data.get("tests", []):
            if test.get("outcome") == "failed":
                call = test.get("call", {})

                failure = TestFailure(
                    test_name=test.get("nodeid", "").split("::")[-1],
                    error_type=call.get("crash", {}).get("exc_type", "Unknown"),
                    error_message=call.get("crash", {}).get("message", ""),
                    stack_trace=call.get("longrepr", ""),
                    file_path=test.get("nodeid", "").split("::")[0],
                    line_number=test.get("lineno", 0),
                    test_code="",  # Not available in JSON report
                    source_code="",
                )

                failures.append(failure)

        return failures
    except Exception as e:
        logger.error(f"Error parsing JSON report: {e}")
        return []


def check_coverage() -> dict[str, Any]:
    """Check test coverage.

    Returns:
        Dictionary with coverage information.
    """
    # This would integrate with pytest-cov
    return {"passed": True, "message": "Coverage check not implemented yet"}


def check_ruff() -> dict[str, Any]:
    """Run Ruff linter check.

    Returns:
        Dictionary with linter results.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["ruff", "check", "apps/api/app"], capture_output=True, text=True
        )

        return {
            "passed": result.returncode == 0,
            "message": "No issues found"
            if result.returncode == 0
            else f"Issues found: {result.stdout}",
        }
    except Exception as e:
        return {"passed": False, "message": f"Error running Ruff: {e}"}


def check_mypy() -> dict[str, Any]:
    """Run MyPy type checker.

    Returns:
        Dictionary with type check results.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["mypy", "--config-file", "mypy.ini", "apps/api/app"],
            capture_output=True,
            text=True,
        )

        return {
            "passed": result.returncode == 0,
            "message": "No type errors"
            if result.returncode == 0
            else f"Type errors found: {result.stdout}",
        }
    except Exception as e:
        return {"passed": False, "message": f"Error running MyPy: {e}"}


def check_bandit() -> dict[str, Any]:
    """Run Bandit security scanner.

    Returns:
        Dictionary with security scan results.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["bandit", "-r", "apps/api/app", "-ll"], capture_output=True, text=True
        )

        return {
            "passed": result.returncode == 0,
            "message": "No security issues"
            if result.returncode == 0
            else f"Security issues found: {result.stdout}",
        }
    except FileNotFoundError:
        return {"passed": True, "message": "Bandit not installed (optional)"}
    except Exception as e:
        return {"passed": False, "message": f"Error running Bandit: {e}"}


def check_safety() -> dict[str, Any]:
    """Check for dependency vulnerabilities.

    Returns:
        Dictionary with vulnerability scan results.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["safety", "check", "--json"], capture_output=True, text=True
        )

        # Safety returns non-zero on vulnerabilities
        vulnerabilities = json.loads(result.stdout) if result.stdout else []

        return {
            "passed": len(vulnerabilities) == 0,
            "message": "No vulnerabilities"
            if len(vulnerabilities) == 0
            else f"{len(vulnerabilities)} vulnerabilities found",
        }
    except FileNotFoundError:
        return {"passed": True, "message": "Safety not installed (optional)"}
    except Exception as e:
        return {"passed": False, "message": f"Error running Safety: {e}"}
