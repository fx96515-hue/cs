"""Automated code fixing with rollback capability."""

import ast
import difflib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AutoFixer:
    """Automatically applies fixes suggested by AI."""

    def __init__(self, repo_root: Path):
        """Initialize the auto-fixer.

        Args:
            repo_root: Root directory of the repository.
        """
        self.repo_root = Path(repo_root)
        self.backup_dir = self.repo_root / ".qa_backups"
        self.backup_dir.mkdir(exist_ok=True)

    def apply_fix(
        self,
        file_path: str,
        fix_code: str,
        confidence_threshold: float = 80.0,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Apply AI-suggested fix to source code.

        Args:
            file_path: Path to file to fix (relative to repo root)
            fix_code: Complete fixed code or patch
            confidence_threshold: Min confidence to auto-apply (0-100)
            dry_run: If True, show changes but don't apply

        Returns:
            Dictionary containing:
                - applied: bool - Whether fix was applied
                - backup_path: str - Path to backup file
                - changes: str - Diff of changes
                - reason: str - Reason for result
                - dry_run: bool - Whether this was a dry run (optional)
        """
        full_path = self.repo_root / file_path

        if not full_path.exists():
            return {"applied": False, "reason": "File not found"}

        # Backup original
        backup_path = self._backup_file(full_path)

        try:
            # Validate syntax before applying
            if file_path.endswith(".py"):
                try:
                    ast.parse(fix_code)  # Will raise SyntaxError if invalid
                except SyntaxError as e:
                    return {
                        "applied": False,
                        "reason": f"Invalid syntax in fix: {e}",
                        "backup_path": str(backup_path),
                    }

            if dry_run:
                diff = self._generate_diff(full_path, fix_code)
                return {
                    "applied": False,
                    "dry_run": True,
                    "changes": diff,
                    "backup_path": str(backup_path),
                    "reason": "Dry run - no changes applied",
                }

            # Apply fix
            full_path.write_text(fix_code)

            return {
                "applied": True,
                "backup_path": str(backup_path),
                "changes": self._generate_diff(backup_path, fix_code),
                "reason": "Fix applied successfully",
            }

        except Exception as e:
            return {
                "applied": False,
                "reason": f"Error applying fix: {e}",
                "backup_path": str(backup_path),
            }

    def rollback(self, backup_path: str) -> bool:
        """Rollback to backup if fix caused issues.

        Args:
            backup_path: Path to backup file.

        Returns:
            True if rollback was successful, False otherwise.
        """
        try:
            backup = Path(backup_path)
            if not backup.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Extract original filename from backup
            # Format: filename.YYYYMMDD_HHMMSS.backup
            name_parts = backup.name.rsplit(".", 2)
            if len(name_parts) != 3 or name_parts[2] != "backup":
                logger.error(f"Invalid backup filename format: {backup.name}")
                return False

            original_name = name_parts[0]

            # Find the original file in repo
            original = self._find_original_file(original_name)
            if not original:
                logger.error(f"Could not find original file for: {original_name}")
                return False

            original.write_text(backup.read_text())
            logger.info(f"Successfully rolled back {original} from {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def _find_original_file(self, filename: str) -> Path | None:
        """Find the original file in the repository by filename.

        Args:
            filename: Name of the file to find.

        Returns:
            Path to the file if found, None otherwise.
        """
        # Search in common locations
        search_paths = [
            self.repo_root / "apps/api" / "app",
            self.repo_root / "apps/api" / "tests",
            self.repo_root / "apps/api",
        ]

        for search_path in search_paths:
            for path in search_path.rglob(filename):
                if path.is_file():
                    return path

        return None

    def _backup_file(self, file_path: Path) -> Path:
        """Create timestamped backup of file.

        Args:
            file_path: Path to file to backup.

        Returns:
            Path to backup file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{file_path.name}.{timestamp}.backup"
        backup_path.write_text(file_path.read_text())
        return backup_path

    def _generate_diff(self, original: Path, new_content: str) -> str:
        """Generate unified diff.

        Args:
            original: Path to original file.
            new_content: New content to compare.

        Returns:
            Unified diff as string.
        """
        original_lines = original.read_text().splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=str(original),
            tofile=f"{original} (fixed)",
        )
        return "".join(diff)
