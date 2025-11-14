"""
Local filesystem implementation of file organization and restoration.

This module provides concrete implementation for organizing and restoring files
on the local filesystem, with backup management via .backup/file_paths.json.
"""

import json
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fileorg.organizer.ports import (
    ExecutionResult,
    FilePathBackup,
    FilePathRecord,
    IFileOrganizer,
    OperationStatus,
)

logger = logging.getLogger(__name__)


class LocalFileOrganizer(IFileOrganizer):
    """
    Local filesystem implementation of file organization and restoration.

    Handles file movements, backup creation, and restoration operations
    on the local filesystem with comprehensive error handling.

    Usage:
        ```python
        organizer = LocalFileOrganizer()
        result = organizer.execute(classification_output, "C:/Users/user/Documents")
        ```
    """

    def __init__(self):
        """Initialize local file organizer."""
        pass

    def execute(
        self,
        classification_output: Any,
        root_dir: str,
        dry_run: bool = False,
    ) -> ExecutionResult:
        """
        Execute file organization with backup creation.

        Args:
            classification_output: Classification results with path_mappings
            root_dir: Root directory for file organization
            dry_run: If True, simulate without actual file movements

        Returns:
            ExecutionResult with operation statistics and details

        Raises:
            ValueError: If classification_output is invalid
            IOError: If unable to access root directory
        """
        start_time = time.time()

        # Validate inputs
        if not hasattr(classification_output, "path_mappings"):
            raise ValueError("classification_output must have path_mappings attribute")

        root_path = Path(root_dir).resolve()
        if not root_path.exists():
            raise IOError(f"Root directory does not exist: {root_dir}")

        # Prepare backup directory (create even in preview mode)
        backup_dir = root_path / ".backup"
        backup_dir.mkdir(exist_ok=True)

        # Prepare file path tracking
        path_mappings = classification_output.path_mappings
        file_path_records = []
        operations = []

        # Process each file mapping
        for _old_path_str, file_mapping in path_mappings.items():
            old_path = Path(file_mapping.old_path).resolve()
            new_relative_path = file_mapping.new_relative_path
            new_path = root_path / new_relative_path

            # Convert to relative paths for backup (relative to root_dir)
            try:
                old_path_relative = old_path.relative_to(root_path)
            except ValueError:
                # If old_path is outside root_path, use absolute path as fallback
                old_path_relative = old_path

            # Track paths for backup (using relative paths)
            file_path_record = FilePathRecord(
                initial_path=str(old_path_relative),
                original=str(old_path_relative),
                new=str(new_relative_path),
            )
            file_path_records.append(file_path_record)

            # Execute or simulate file movement
            if not dry_run:
                success, error, actual_new_path = self._move_file_with_conflict_handling(old_path, new_path)
                status = "success" if success else "failed"
            else:
                # Dry run - just validate
                actual_new_path = str(new_path)
                if not old_path.exists():
                    status = "skipped"
                    error = "File not found"
                else:
                    status = "success"
                    error = None

            # Record operation status
            op_status = OperationStatus(
                old_path=str(old_path),
                new_path=actual_new_path,
                status=status,
                error=error,
                category=file_mapping.category,
            )
            operations.append(op_status)

        # Create backup record (always create, even in preview mode)
        backup = FilePathBackup(
            timestamp=datetime.now().isoformat(),
            file_paths=file_path_records,
        )
        self._save_backup(backup, backup_dir / "file_paths.json")

        # Clean up empty directories (only in non-preview mode)
        if not dry_run:
            self._cleanup_empty_directories(root_path)

        # Calculate statistics
        success_count = sum(1 for op in operations if op.status == "success")
        failed_count = sum(1 for op in operations if op.status == "failed")
        skipped_count = sum(1 for op in operations if op.status == "skipped")

        execution_time = time.time() - start_time

        return ExecutionResult(
            total_count=len(operations),
            success_count=success_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            operations=operations,
            backup_dir=str(backup_dir),
            execution_time=execution_time,
        )

    def restore(self, root_dir: str) -> Dict[str, Any]:
        """
        Restore files to their original locations.

        Args:
            root_dir: Root directory containing .backup folder

        Returns:
            Dictionary with restoration statistics and errors

        Raises:
            FileNotFoundError: If .backup/file_paths.json doesn't exist
            ValueError: If backup data is corrupted
        """
        root_path = Path(root_dir).resolve()
        backup_file = root_path / ".backup" / "file_paths.json"

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        # Load backup data
        backup = self._load_backup(backup_file)

        # Track restoration results
        restored_count = 0
        failed_count = 0
        skipped_count = 0
        errors = []

        # Restore each file
        for record in backup.file_paths:
            # Convert relative paths back to absolute paths
            initial_path_rel = Path(record.initial_path)
            new_path_rel = Path(record.new)

            # Resolve to absolute paths relative to root_dir
            if initial_path_rel.is_absolute():
                initial_path = initial_path_rel  # Fallback for old absolute paths
            else:
                initial_path = root_path / initial_path_rel

            if new_path_rel.is_absolute():
                new_path = new_path_rel  # Fallback for old absolute paths
            else:
                new_path = root_path / new_path_rel

            # Try to locate the file (might have been manually moved)
            current_path = self._find_file(new_path, root_path)

            if current_path is None:
                skipped_count += 1
                errors.append(f"File not found: {new_path}")
                continue

            # Restore to initial location
            try:
                # Create parent directory if needed
                initial_path.parent.mkdir(parents=True, exist_ok=True)

                # Handle conflicts at restoration target
                actual_target = self._resolve_conflict(initial_path)

                # Move file back
                shutil.move(str(current_path), str(actual_target))
                restored_count += 1
                logger.info(f"Restored: {current_path} -> {actual_target}")
            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to restore {current_path}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Clean up empty directories
        self._cleanup_empty_directories(root_path)

        return {
            "total": len(backup.file_paths),
            "restored": restored_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "errors": errors,
        }

    def _move_file_with_conflict_handling(self, old_path: Path, new_path: Path) -> Tuple[bool, Optional[str], str]:
        """
        Move a file with automatic conflict resolution.

        Args:
            old_path: Source file path
            new_path: Target file path

        Returns:
            Tuple of (success, error_message, actual_new_path)
        """
        try:
            # Check if source exists
            if not old_path.exists():
                return False, "File not found", str(new_path)

            # Create target directory
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # Resolve conflicts
            actual_new_path = self._resolve_conflict(new_path)

            # Move file
            shutil.move(str(old_path), str(actual_new_path))
            logger.info(f"Moved: {old_path} -> {actual_new_path}")

            return True, None, str(actual_new_path)

        except Exception as e:
            error_msg = f"Failed to move file: {str(e)}"
            logger.error(f"{error_msg} (from {old_path} to {new_path})")
            return False, error_msg, str(new_path)

    def _resolve_conflict(self, path: Path) -> Path:
        """
        Resolve filename conflict by appending _1, _2, etc.

        Args:
            path: Target file path

        Returns:
            Available file path (may be modified to avoid conflict)
        """
        if not path.exists():
            return path

        # Extract filename components
        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        # Try incrementing numbers
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def _find_file(self, expected_path: Path, search_root: Path) -> Optional[Path]:
        """
        Find a file that may have been manually moved.

        Args:
            expected_path: Expected file location
            search_root: Root directory to search within

        Returns:
            Actual file path if found, None otherwise
        """
        # First check expected location
        if expected_path.exists():
            return expected_path

        # Search for file with same name in the organized area
        # This is a simplified search - could be enhanced with file hash matching
        filename = expected_path.name

        # Search within the root directory
        for path in search_root.rglob(filename):
            if path.is_file():
                return path

        return None

    def _cleanup_empty_directories(self, root_path: Path) -> None:
        """
        Remove empty directories created during file operations.

        Args:
            root_path: Root directory to clean up
        """
        # Get all directories, sorted by depth (deepest first)
        all_dirs = sorted(
            [p for p in root_path.rglob("*") if p.is_dir() and p.name != ".backup"],
            key=lambda p: len(p.parts),
            reverse=True,
        )

        for dir_path in all_dirs:
            try:
                # Only remove if empty and not the root
                if dir_path != root_path and not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    logger.info(f"Removed empty directory: {dir_path}")
            except Exception as e:
                logger.warning(f"Could not remove directory {dir_path}: {str(e)}")

    def _save_backup(self, backup: FilePathBackup, backup_file: Path) -> None:
        """
        Save backup data to JSON file.

        Args:
            backup: FilePathBackup instance
            backup_file: Path to save backup JSON

        Raises:
            IOError: If unable to write backup file
        """
        try:
            backup_data = {
                "timestamp": backup.timestamp,
                "file_paths": [
                    {
                        "initial_path": record.initial_path,
                        "original": record.original,
                        "new": record.new,
                    }
                    for record in backup.file_paths
                ],
            }

            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=4, ensure_ascii=False)

            logger.info(f"Saved backup to: {backup_file}")

        except Exception as e:
            raise IOError(f"Failed to save backup file: {str(e)}") from e

    def _load_backup(self, backup_file: Path) -> FilePathBackup:
        """
        Load backup data from JSON file.

        Args:
            backup_file: Path to backup JSON file

        Returns:
            FilePathBackup instance

        Raises:
            ValueError: If backup data is corrupted
        """
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            file_paths_data = data.get("file_paths", [])
            file_path_records = [
                FilePathRecord(
                    initial_path=record.get("initial_path", ""),
                    original=record.get("original", ""),
                    new=record.get("new", ""),
                )
                for record in file_paths_data
            ]

            return FilePathBackup(
                timestamp=data.get("timestamp", ""),
                file_paths=file_path_records,
            )

        except Exception as e:
            raise ValueError(f"Failed to load backup file: {str(e)}") from e
