"""Tests for QA auto-fixer."""

import pytest
from pathlib import Path
import tempfile
import shutil

from app.qa.auto_fixer import AutoFixer


@pytest.fixture
def temp_repo():
    """Create a temporary repository for testing."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create a test file
    test_file = temp_dir / "test_file.py"
    test_file.write_text("def test_function():\n    return 42\n")

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


def test_auto_fixer_initialization(temp_repo):
    """Test AutoFixer initialization."""
    fixer = AutoFixer(repo_root=temp_repo)

    assert fixer.repo_root == temp_repo
    assert fixer.backup_dir.exists()
    assert fixer.backup_dir == temp_repo / ".qa_backups"


def test_apply_fix_dry_run(temp_repo):
    """Test applying a fix in dry-run mode."""
    fixer = AutoFixer(repo_root=temp_repo)

    original_code = "def test_function():\n    return 42\n"
    fixed_code = "def test_function():\n    return 43\n"

    result = fixer.apply_fix(
        file_path="test_file.py", fix_code=fixed_code, dry_run=True
    )

    assert result["applied"] is False
    assert result["dry_run"] is True
    assert "backup_path" in result
    assert "changes" in result

    # Original file should be unchanged
    test_file = temp_repo / "test_file.py"
    assert test_file.read_text() == original_code


def test_apply_fix_creates_backup(temp_repo):
    """Test that applying a fix creates a backup."""
    fixer = AutoFixer(repo_root=temp_repo)

    original_code = "def test_function():\n    return 42\n"
    fixed_code = "def test_function():\n    return 43\n"

    result = fixer.apply_fix(
        file_path="test_file.py", fix_code=fixed_code, dry_run=False
    )

    assert result["applied"] is True
    assert "backup_path" in result

    # Check backup exists and contains original code
    backup_path = Path(result["backup_path"])
    assert backup_path.exists()
    assert backup_path.read_text() == original_code

    # Check file was updated
    test_file = temp_repo / "test_file.py"
    assert test_file.read_text() == fixed_code


def test_apply_fix_invalid_syntax(temp_repo):
    """Test applying a fix with invalid Python syntax."""
    fixer = AutoFixer(repo_root=temp_repo)

    invalid_code = "def test_function(\n    return 42\n"  # Missing closing paren

    result = fixer.apply_fix(
        file_path="test_file.py", fix_code=invalid_code, dry_run=False
    )

    assert result["applied"] is False
    assert "Invalid syntax" in result["reason"]


def test_apply_fix_file_not_found(temp_repo):
    """Test applying a fix to a non-existent file."""
    fixer = AutoFixer(repo_root=temp_repo)

    result = fixer.apply_fix(
        file_path="nonexistent.py", fix_code="# some code", dry_run=False
    )

    assert result["applied"] is False
    assert result["reason"] == "File not found"


def test_generate_diff(temp_repo):
    """Test diff generation."""
    fixer = AutoFixer(repo_root=temp_repo)

    test_file = temp_repo / "test_file.py"
    new_content = "def test_function():\n    return 43\n"

    diff = fixer._generate_diff(test_file, new_content)

    assert "@@" in diff  # Unified diff marker
    assert "-    return 42" in diff
    assert "+    return 43" in diff
