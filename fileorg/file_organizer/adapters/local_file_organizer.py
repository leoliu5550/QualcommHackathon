"""
Local filesystem file organizer implementation.

Provides file organization operations on the local filesystem,
including file movement, conflict resolution, and restoration integration.
"""

import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from fileorg.file_organizer.ports import (
    ExecutionResult,
    IFileExecutor,
    OperationStatus,
)
from fileorg.restoration.adapters.json_restoration_manager import (
    JsonRestorationManager,
)
from fileorg.restoration.application.restoration_use_case import RestorationUseCase


class LocalFileOrganizer(IFileExecutor):
    """
    Local filesystem implementation of file organizer.

    Moves files on the local filesystem according to classification results,
    with automatic conflict resolution and restoration point integration.

    Usage:
        ```python
        organizer = LocalFileOrganizer()
        result = organizer.execute(
            classification_output,
            target_dir="C:/Organized",
            root_dir="C:/Documents"
        )
        print(f"Moved {result.success_count}/{result.total_count} files")
        ```
    """

    def __init__(self, restoration_manager: Optional[JsonRestorationManager] = None):
        """
        Initialize local file organizer.

        Args:
            restoration_manager: Optional restoration manager (auto-created if None)
        """
        self._restoration_manager = restoration_manager or JsonRestorationManager()
        self._restoration_use_case = RestorationUseCase(self._restoration_manager)

    def execute(
        self,
        classification_output: Any,
        target_dir: str,
        root_dir: str,
        dry_run: bool = False,
        create_restoration_point: bool = True,
        manifest_path: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute file organization on local filesystem.

        See IFileExecutor.execute for full documentation.
        """
        start_time = time.time()

        # Validate classification output
        if not hasattr(classification_output, "path_mappings"):
            raise ValueError("classification_output must have 'path_mappings' attribute")

        path_mappings = classification_output.path_mappings
        if not isinstance(path_mappings, dict):
            raise ValueError("path_mappings must be a dictionary")

        logger.info(f"Starting file organization: {len(path_mappings)} files, target_dir={target_dir}, dry_run={dry_run}")

        # Convert to absolute paths
        target_dir_abs = str(Path(target_dir).resolve())
        root_dir_abs = str(Path(root_dir).resolve())

        # Create restoration point if requested
        actual_manifest_path = None
        if create_restoration_point and not dry_run:
            if manifest_path is None:
                # Auto-generate manifest path in target_dir
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                manifest_path = str(Path(target_dir_abs) / f"restoration_{timestamp}.json")

            try:
                self._restoration_use_case.create_and_save_restoration_point(
                    classification_output=classification_output,
                    target_dir=target_dir_abs,
                    root_dir=root_dir_abs,
                    manifest_path=manifest_path,
                    validate=True,
                )
                actual_manifest_path = manifest_path
                logger.info(f"Created restoration point: {manifest_path}")
            except Exception as e:
                logger.error(f"Failed to create restoration point: {e}")
                # Continue with execution even if restoration point fails
                # User can still manually undo operations

        # Execute file operations
        operations: list[OperationStatus] = []
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for old_path, file_mapping in path_mappings.items():
            # Compose new_path (must match Task4 logic)
            new_path = self._compose_new_path(target_dir_abs, file_mapping.new_relative_path)

            # Check if source file exists
            old_path_obj = Path(old_path)
            if not old_path_obj.exists():
                status = OperationStatus(
                    old_path=old_path,
                    new_path=new_path,
                    status="skipped",
                    error="Source file not found",
                    category=file_mapping.category,
                )
                operations.append(status)
                skipped_count += 1
                logger.warning(f"Skipped (not found): {old_path}")
                continue

            # Dry-run mode: simulate without actual movement
            if dry_run:
                status = OperationStatus(
                    old_path=old_path,
                    new_path=new_path,
                    status="success",
                    error=None,
                    category=file_mapping.category,
                )
                operations.append(status)
                success_count += 1
                logger.info(f"[DRY-RUN] Would move: {old_path} -> {new_path}")
                continue

            # Execute actual file movement
            success, error, actual_new_path = self.move_file(old_path, new_path, handle_conflict=True)

            if success:
                status = OperationStatus(
                    old_path=old_path,
                    new_path=actual_new_path,  # Use actual path (may differ due to conflict)
                    status="success",
                    error=None,
                    category=file_mapping.category,
                )
                operations.append(status)
                success_count += 1
                logger.info(f"Moved: {old_path} -> {actual_new_path}")
            else:
                status = OperationStatus(
                    old_path=old_path,
                    new_path=new_path,
                    status="failed",
                    error=error,
                    category=file_mapping.category,
                )
                operations.append(status)
                failed_count += 1
                logger.error(f"Failed to move {old_path}: {error}")

        # Update restoration point with execution status
        if actual_manifest_path and not dry_run:
            try:
                self._update_restoration_point(actual_manifest_path, operations)
                logger.info("Updated restoration point with execution status")
            except Exception as e:
                logger.error(f"Failed to update restoration point: {e}")

        execution_time = time.time() - start_time

        result = ExecutionResult(
            total_count=len(path_mappings),
            success_count=success_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            operations=operations,
            restoration_manifest_path=actual_manifest_path,
            execution_time=execution_time,
        )

        logger.info(f"Execution complete: {success_count} success, {failed_count} failed, {skipped_count} skipped (time: {execution_time:.2f}s)")

        return result

    def move_file(
        self,
        old_path: str,
        new_path: str,
        handle_conflict: bool = True,
    ) -> tuple[bool, Optional[str], str]:
        """
        Move a single file on local filesystem.

        See IFileExecutor.move_file for full documentation.
        """
        old_path_obj = Path(old_path)
        new_path_obj = Path(new_path)

        # Check if source exists
        if not old_path_obj.exists():
            return False, "Source file not found", new_path

        # Create target directory
        if not self.create_target_directory(str(new_path_obj.parent)):
            return False, f"Failed to create target directory: {new_path_obj.parent}", new_path

        # Handle filename conflict
        actual_new_path = new_path_obj
        if new_path_obj.exists():
            if handle_conflict:
                actual_new_path = self._resolve_conflict(new_path_obj)
                logger.debug(f"Conflict resolved: {new_path} -> {actual_new_path}")
            else:
                return False, "Target file already exists", new_path

        # Move file
        try:
            shutil.move(str(old_path_obj), str(actual_new_path))
            return True, None, str(actual_new_path)
        except Exception as e:
            return False, f"Move failed: {e}", new_path

    def create_target_directory(
        self,
        path: str,
    ) -> bool:
        """
        Create directory on local filesystem.

        See IFileExecutor.create_target_directory for full documentation.
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False

    @staticmethod
    def _compose_new_path(target_dir: str, new_relative_path: str) -> str:
        """
        Compose absolute new_path from target_dir and new_relative_path.

        Args:
            target_dir: Absolute target directory path
            new_relative_path: Relative path from FileMapping (e.g., "Category/file.pdf")

        Returns:
            Absolute path (target_dir / new_relative_path)
        """
        target_path = Path(target_dir).resolve()
        new_path = target_path / new_relative_path
        return str(new_path.resolve())

    @staticmethod
    def _resolve_conflict(new_path: Path) -> Path:
        """
        Resolve filename conflict by appending _1, _2, etc.

        Args:
            new_path: Path that already exists

        Returns:
            Available path with numeric suffix

        Example:
            report.pdf -> report_1.pdf -> report_2.pdf
        """
        stem = new_path.stem
        suffix = new_path.suffix
        parent = new_path.parent

        counter = 1
        while True:
            candidate = parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def _update_restoration_point(
        self,
        manifest_path: str,
        operations: list[OperationStatus],
    ) -> None:
        """
        Update restoration point with execution status.

        Marks operations as executed in the restoration manifest.

        Args:
            manifest_path: Path to restoration manifest
            operations: List of operation statuses

        Note:
            Only successful operations are marked as executed.
        """
        # Load existing restoration point
        restoration_point = self._restoration_manager.load_restoration_point(manifest_path)

        # Create lookup dict for quick access
        operation_lookup = {op.old_path: op for op in operations}

        # Update executed status
        for file_op in restoration_point.file_operations:
            if file_op.old_path in operation_lookup:
                op_status = operation_lookup[file_op.old_path]
                if op_status.status == "success":
                    file_op.executed = True
                    file_op.error = None
                    # Update new_path in case conflict was resolved
                    file_op.new_path = op_status.new_path
                elif op_status.status == "failed":
                    file_op.executed = False
                    file_op.error = op_status.error

        # Save updated restoration point
        self._restoration_manager.save_restoration_point(restoration_point, manifest_path)
