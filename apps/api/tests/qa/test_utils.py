"""Tests for QA utility functions."""

from pathlib import Path
import tempfile

from app.qa.failure_analyzer import TestFailure
from app.qa.utils import parse_pytest_output, _read_file_section


def test_test_failure_dataclass():
    """Test TestFailure dataclass creation."""
    failure = TestFailure(
        test_name="test_example",
        error_type="AssertionError",
        error_message="Expected 1, got 2",
        stack_trace="traceback here",
        file_path="tests/test_example.py",
        line_number=42,
        test_code="def test_example(): ...",
        source_code="def example(): ...",
    )

    assert failure.test_name == "test_example"
    assert failure.error_type == "AssertionError"
    assert failure.line_number == 42


def test_parse_pytest_output_no_failures():
    """Test parsing pytest output with no failures."""
    output = """
============================= test session starts ==============================
collected 5 items

tests/test_example.py .....                                              [100%]

============================== 5 passed in 0.01s ===============================
"""

    failures = parse_pytest_output(output)
    assert len(failures) == 0


def test_parse_pytest_output_with_failures():
    """Test parsing pytest output with failures."""
    output = """
============================= test session starts ==============================
collected 2 items

FAILED tests/test_example.py::test_addition - AssertionError: Expected 3, got 2
FAILED tests/test_example.py::test_subtraction - ValueError: Invalid operation
"""

    failures = parse_pytest_output(output)
    assert len(failures) == 2


def test_read_file_section_nonexistent():
    """Test reading from a non-existent file."""
    result = _read_file_section("nonexistent.py", "test_function")
    assert result == ""


def test_read_file_section_existing():
    """Test reading a function from an existing file."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
def test_function():
    return 42

def another_function():
    return 43
""")
        temp_path = f.name

    try:
        result = _read_file_section(temp_path, "test_function")
        assert "def test_function" in result
        assert "return 42" in result
        # Should not include the other function
        assert "another_function" not in result
    finally:
        Path(temp_path).unlink()
