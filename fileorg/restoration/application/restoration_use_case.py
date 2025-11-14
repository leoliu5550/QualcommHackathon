"""
Restoration use case - business logic orchestration.

Coordinates restoration operations through the restoration manager,
providing a high-level interface for creating and restoring file operations.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from fileorg.restoration.ports import IRestorationManager, RestorationPoint


class RestorationUseCase:
    """
    Orchestrates file restoration operations.

    Provides business logic layer for creating restoration points,
    validating them, and executing file rollback operations.

    Usage:
        ```python
        from fileorg.restoration.adapters import JsonRestorationManager

        manager = JsonRestorationManager()
        use_case = RestorationUseCase(manager)

        # Create and save restoration point
        point = use_case.create_and_save_restoration_point(
            classification_output,
            target_dir="C:/Organized",
            root_dir="C:/Documents",
            manifest_path="C:/restore.json"
        )

        # Later, restore files
        result = use_case.restore_files("C:/restore.json")
        print(f"Restored {result['restored']} files")
        ```
    """

    def __init__(self, restoration_manager: IRestorationManager):
        """
        Initialize use case with restoration manager.

        Args:
            restoration_manager: Implementation of IRestorationManager (e.g., JsonRestorationManager)
        """
        self._manager = restoration_manager

    def create_and_save_restoration_point(
        self,
        classification_output: Any,
        target_dir: str,
        root_dir: str,
        manifest_path: str,
        timestamp: Optional[str] = None,
        validate: bool = True,
    ) -> RestorationPoint:
        """
        Create restoration point and save to manifest file.

        Convenience method that combines create, validate, and save operations.

        Args:
            classification_output: Output from Task3 classifier
            target_dir: Target directory for organized files
            root_dir: Original scan root directory
            manifest_path: Path where manifest should be saved
            timestamp: Optional ISO 8601 timestamp
            validate: Whether to validate before saving (default: True)

        Returns:
            Created RestorationPoint

        Raises:
            ValueError: If validation fails or inputs are invalid
            IOError: If unable to save manifest
        """
        logger.info(f"Creating restoration point for {len(classification_output.path_mappings)} files")

        # Create restoration point
        restoration_point = self._manager.create_restoration_point(
            classification_output=classification_output,
            target_dir=target_dir,
            root_dir=root_dir,
            timestamp=timestamp,
        )

        # Validate if requested
        if validate:
            if not self._manager.validate_restoration_point(restoration_point):
                raise ValueError("Restoration point validation failed")
            logger.info("Restoration point validation passed")

        # Save to manifest
        self._manager.save_restoration_point(restoration_point, manifest_path)

        logger.info(f"Restoration point saved to {manifest_path}")
        return restoration_point

    def restore_files(
        self,
        manifest_path: str,
        confirm: bool = True,
    ) -> Dict[str, Any]:
        """
        Restore files to original locations based on manifest.

        Executes rollback of file organization operations.

        Args:
            manifest_path: Path to the restoration manifest
            confirm: Whether to require confirmation (for CLI integration)

        Returns:
            Dictionary with restoration results:
                {
                    "total": int,
                    "restored": int,
                    "failed": int,
                    "skipped": int,
                    "errors": List[str]
                }

        Raises:
            FileNotFoundError: If manifest doesn't exist
        """
        manifest_path_obj = Path(manifest_path)
        if not manifest_path_obj.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        logger.info(f"Starting restoration from manifest: {manifest_path}")

        # Load restoration point to check details
        restoration_point = self._manager.load_restoration_point(manifest_path)
        logger.info(f"Loaded restoration point (timestamp: {restoration_point.timestamp}, operations: {len(restoration_point.file_operations)})")

        # Execute restoration
        result = self._manager.restore(manifest_path)

        # Log summary
        logger.info(f"Restoration completed: {result['restored']} restored, {result['failed']} failed, {result['skipped']} skipped")

        if result["errors"]:
            logger.warning(f"Encountered {len(result['errors'])} errors during restoration")

        return result

    def validate_manifest(
        self,
        manifest_path: str,
    ) -> bool:
        """
        Validate restoration manifest without executing restoration.

        Loads manifest and validates restoration point integrity.

        Args:
            manifest_path: Path to the restoration manifest

        Returns:
            True if manifest is valid and restorable, False otherwise
        """
        try:
            restoration_point = self._manager.load_restoration_point(manifest_path)
            is_valid = self._manager.validate_restoration_point(restoration_point)

            if is_valid:
                logger.info(f"Manifest validation passed: {manifest_path}")
            else:
                logger.warning(f"Manifest validation failed: {manifest_path}")

            return is_valid
        except Exception as e:
            logger.error(f"Error validating manifest {manifest_path}: {e}")
            return False

    def get_restoration_point_info(
        self,
        manifest_path: str,
    ) -> Dict[str, Any]:
        """
        Get information about a restoration point without executing it.

        Useful for displaying restoration point details to users.

        Args:
            manifest_path: Path to the restoration manifest

        Returns:
            Dictionary with restoration point information:
                {
                    "timestamp": str,
                    "root_dir": str,
                    "target_dir": str,
                    "total_operations": int,
                    "executed_operations": int,
                    "categories": List[str],
                    "metadata": Optional[Dict]
                }

        Raises:
            FileNotFoundError: If manifest doesn't exist
        """
        restoration_point = self._manager.load_restoration_point(manifest_path)

        executed_count = sum(1 for op in restoration_point.file_operations if op.executed)

        categories = list({op.category for op in restoration_point.file_operations})

        info = {
            "timestamp": restoration_point.timestamp,
            "root_dir": restoration_point.root_dir,
            "target_dir": restoration_point.target_dir,
            "total_operations": len(restoration_point.file_operations),
            "executed_operations": executed_count,
            "categories": sorted(categories),
            "metadata": restoration_point.metadata,
        }

        return info
