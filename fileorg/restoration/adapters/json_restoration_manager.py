"""
JSON-based restoration manager implementation.

Provides JSON persistence for restoration points, enabling save/load
of restoration manifests and file rollback operations.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from fileorg.restoration.ports import (
    FileOperation,
    IRestorationManager,
    RestorationPoint,
)


class JsonRestorationManager(IRestorationManager):
    """
    JSON-based implementation of restoration manager.

    Persists restoration points as JSON files and provides rollback functionality
    by moving files back to their original locations.

    Usage:
        ```python
        manager = JsonRestorationManager()

        # Create restoration point
        point = manager.create_restoration_point(
            classification_output,
            target_dir="C:/Organized",
            root_dir="C:/Documents"
        )

        # Save to manifest
        manager.save_restoration_point(point, "restore.json")

        # Later, restore files
        result = manager.restore("restore.json")
        ```
    """

    def create_restoration_point(
        self,
        classification_output: Any,
        target_dir: str,
        root_dir: str,
        timestamp: Optional[str] = None,
    ) -> RestorationPoint:
        """
        Create restoration point from Task3 classification output.

        Converts ClassificationOutput.path_mappings into FileOperation records
        with proper path composition.

        Args:
            classification_output: Must have path_mappings attribute (Dict[str, FileMapping])
            target_dir: Target directory for organized files
            root_dir: Original scan root directory
            timestamp: ISO 8601 timestamp (auto-generated if None)

        Returns:
            RestorationPoint with all file operations

        Raises:
            ValueError: If classification_output is missing required attributes
        """
        if not hasattr(classification_output, "path_mappings"):
            raise ValueError("classification_output must have 'path_mappings' attribute")

        path_mappings = classification_output.path_mappings
        if not isinstance(path_mappings, dict):
            raise ValueError("path_mappings must be a dictionary")

        # Generate timestamp if not provided
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        # Convert target_dir and root_dir to absolute paths
        target_dir_path = Path(target_dir).resolve()
        root_dir_path = Path(root_dir).resolve()

        # Create file operations from path mappings
        file_operations: list[FileOperation] = []

        for old_path, file_mapping in path_mappings.items():
            # Compose new_path: target_dir / new_relative_path
            # CRITICAL: This must match Task5's path composition logic
            new_path = self._compose_new_path(str(target_dir_path), file_mapping.new_relative_path)

            operation = FileOperation(
                old_path=old_path,  # Keep as-is from Task3 (absolute path)
                new_path=new_path,
                category=file_mapping.category,
                executed=False,
                error=None,
            )
            file_operations.append(operation)

        # Extract metadata from classification output if available
        metadata = None
        if hasattr(classification_output, "metadata"):
            metadata = classification_output.metadata

        restoration_point = RestorationPoint(
            timestamp=timestamp,
            root_dir=str(root_dir_path),
            target_dir=str(target_dir_path),
            file_operations=file_operations,
            metadata=metadata,
        )

        logger.info(f"Created restoration point with {len(file_operations)} operations (timestamp: {timestamp})")

        return restoration_point

    def save_restoration_point(
        self,
        restoration_point: RestorationPoint,
        manifest_path: str,
    ) -> None:
        """
        Save restoration point to JSON file.

        Creates parent directories if needed. Serializes all dataclass fields
        to JSON format.

        Args:
            restoration_point: The restoration point to save
            manifest_path: Path where manifest should be saved

        Raises:
            IOError: If unable to write to manifest_path
            ValueError: If restoration_point has invalid data
        """
        manifest_path_obj = Path(manifest_path)

        # Create parent directories if they don't exist
        manifest_path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Convert dataclass to dict for JSON serialization
        manifest_data = {
            "timestamp": restoration_point.timestamp,
            "root_dir": restoration_point.root_dir,
            "target_dir": restoration_point.target_dir,
            "file_operations": [
                {
                    "old_path": op.old_path,
                    "new_path": op.new_path,
                    "category": op.category,
                    "executed": op.executed,
                    "error": op.error,
                }
                for op in restoration_point.file_operations
            ],
            "metadata": restoration_point.metadata,
        }

        try:
            with manifest_path_obj.open("w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved restoration point to {manifest_path}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to save restoration point to {manifest_path}: {e}")
            raise IOError(f"Cannot write to {manifest_path}: {e}") from e

    def load_restoration_point(
        self,
        manifest_path: str,
    ) -> RestorationPoint:
        """
        Load restoration point from JSON manifest.

        Deserializes JSON and reconstructs RestorationPoint with FileOperations.

        Args:
            manifest_path: Path to the manifest file

        Returns:
            Loaded RestorationPoint

        Raises:
            FileNotFoundError: If manifest doesn't exist
            ValueError: If JSON is corrupted or has invalid structure
        """
        manifest_path_obj = Path(manifest_path)

        if not manifest_path_obj.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        try:
            with manifest_path_obj.open("r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest {manifest_path}: {e}")
            raise ValueError(f"Corrupted manifest file: {e}") from e

        # Validate required fields
        required_fields = ["timestamp", "root_dir", "target_dir", "file_operations"]
        for field in required_fields:
            if field not in manifest_data:
                raise ValueError(f"Missing required field in manifest: {field}")

        # Reconstruct FileOperation objects
        file_operations = [
            FileOperation(
                old_path=op_data["old_path"],
                new_path=op_data["new_path"],
                category=op_data["category"],
                executed=op_data.get("executed", False),
                error=op_data.get("error"),
            )
            for op_data in manifest_data["file_operations"]
        ]

        restoration_point = RestorationPoint(
            timestamp=manifest_data["timestamp"],
            root_dir=manifest_data["root_dir"],
            target_dir=manifest_data["target_dir"],
            file_operations=file_operations,
            metadata=manifest_data.get("metadata"),
        )

        logger.info(f"Loaded restoration point from {manifest_path} with {len(file_operations)} operations")

        return restoration_point

    def restore(
        self,
        manifest_path: str,
    ) -> Dict[str, Any]:
        """
        Restore files to original locations based on manifest.

        Moves files from new_path back to old_path for all executed operations.
        Skips operations that were not executed or where files don't exist.

        Args:
            manifest_path: Path to the restoration manifest

        Returns:
            Dictionary with restoration results (total, restored, failed, skipped, errors)
        """
        restoration_point = self.load_restoration_point(manifest_path)

        total = len(restoration_point.file_operations)
        restored = 0
        failed = 0
        skipped = 0
        errors: list[str] = []

        logger.info(f"Starting restoration of {total} operations")

        for operation in restoration_point.file_operations:
            # Skip if not executed
            if not operation.executed:
                skipped += 1
                logger.debug(f"Skipping non-executed operation: {operation.old_path}")
                continue

            new_path = Path(operation.new_path)
            old_path = Path(operation.old_path)

            # Check if new file exists (the file to restore)
            if not new_path.exists():
                error_msg = f"Cannot restore {operation.new_path}: file not found"
                errors.append(error_msg)
                failed += 1
                logger.warning(error_msg)
                continue

            # Create parent directory for old_path if needed
            old_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                # Move file back to original location
                shutil.move(str(new_path), str(old_path))
                restored += 1
                logger.debug(f"Restored: {new_path} -> {old_path}")
            except Exception as e:
                error_msg = f"Failed to restore {operation.new_path}: {e}"
                errors.append(error_msg)
                failed += 1
                logger.error(error_msg)

        result = {
            "total": total,
            "restored": restored,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
        }

        logger.info(f"Restoration complete: {restored} restored, {failed} failed, {skipped} skipped")

        return result

    def validate_restoration_point(
        self,
        restoration_point: RestorationPoint,
    ) -> bool:
        """
        Validate restoration point integrity.

        Checks that:
        - All old_paths exist (source files are present)
        - All paths are valid absolute paths
        - No duplicate operations

        Args:
            restoration_point: The restoration point to validate

        Returns:
            True if valid and restorable, False otherwise
        """
        if not restoration_point.file_operations:
            logger.warning("Restoration point has no file operations")
            return False

        seen_paths = set()

        for operation in restoration_point.file_operations:
            # Check for duplicates
            if operation.old_path in seen_paths:
                logger.error(f"Duplicate operation for path: {operation.old_path}")
                return False
            seen_paths.add(operation.old_path)

            # Validate paths are absolute
            old_path = Path(operation.old_path)
            new_path = Path(operation.new_path)

            if not old_path.is_absolute():
                logger.error(f"old_path is not absolute: {operation.old_path}")
                return False

            if not new_path.is_absolute():
                logger.error(f"new_path is not absolute: {operation.new_path}")
                return False

            # Check if source file exists
            if not old_path.exists():
                logger.warning(f"Source file does not exist: {operation.old_path}")
                # Not a hard failure - file might have been deleted

        logger.info(f"Restoration point validation passed ({len(seen_paths)} operations)")
        return True

    @staticmethod
    def _compose_new_path(target_dir: str, new_relative_path: str) -> str:
        """
        Compose absolute new_path from target_dir and new_relative_path.

        CRITICAL: This logic must match Task5's path composition exactly
        to ensure consistency between restoration point creation and execution.

        Args:
            target_dir: Absolute target directory path
            new_relative_path: Relative path from FileMapping (e.g., "Category/file.pdf")

        Returns:
            Absolute path (target_dir / new_relative_path)
        """
        target_path = Path(target_dir).resolve()
        new_path = target_path / new_relative_path
        return str(new_path.resolve())
