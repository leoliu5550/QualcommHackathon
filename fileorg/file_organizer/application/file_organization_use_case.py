"""
File organization use case - business logic orchestration.

Coordinates file organization operations through the file executor,
providing a high-level interface for organizing files with optional
dry-run and restoration point creation.
"""

from pathlib import Path
from typing import Any, Optional

from loguru import logger

from fileorg.file_organizer.ports import ExecutionResult, IFileExecutor


class FileOrganizationUseCase:
    """
    Orchestrates file organization operations.

    Provides business logic layer for executing file organization,
    validating inputs, and managing restoration points.

    Usage:
        ```python
        from fileorg.file_organizer.adapters import LocalFileOrganizer

        executor = LocalFileOrganizer()
        use_case = FileOrganizationUseCase(executor)

        # Execute organization
        result = use_case.organize_files(
            classification_output,
            target_dir="C:/Organized",
            root_dir="C:/Documents",
            dry_run=False
        )
        print(f"Organized {result.success_count} files")
        ```
    """

    def __init__(self, file_executor: IFileExecutor):
        """
        Initialize use case with file executor.

        Args:
            file_executor: Implementation of IFileExecutor (e.g., LocalFileOrganizer)
        """
        self._executor = file_executor

    def organize_files(
        self,
        classification_output: Any,
        target_dir: str,
        root_dir: str,
        dry_run: bool = False,
        create_restoration_point: bool = True,
        manifest_path: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Organize files according to classification results.

        Main entry point for file organization. Validates inputs,
        executes file operations, and handles restoration point creation.

        Args:
            classification_output: Output from Task3 LLM classifier
            target_dir: Target directory for organized files
            root_dir: Original directory where files were scanned
            dry_run: If True, simulate operations without actual file movement
            create_restoration_point: Whether to create restoration point
            manifest_path: Optional path for restoration manifest

        Returns:
            ExecutionResult with detailed statistics and operation status

        Raises:
            ValueError: If inputs are invalid
            IOError: If unable to access directories

        Example:
            ```python
            result = use_case.organize_files(
                classification_output,
                target_dir="C:/Users/user/Organized",
                root_dir="C:/Users/user/Documents",
                dry_run=True  # Preview mode
            )
            print(f"Would organize {result.total_count} files")
            for op in result.operations:
                print(f"  {op.old_path} -> {op.new_path}")
            ```
        """
        # Validate inputs
        self._validate_inputs(classification_output, target_dir, root_dir)

        # Log operation details
        file_count = len(classification_output.path_mappings)
        logger.info(f"Organizing {file_count} files from {root_dir} to {target_dir}")
        if dry_run:
            logger.info("[DRY-RUN MODE] No files will be actually moved")
        if create_restoration_point and not dry_run:
            logger.info("Restoration point will be created")

        # Execute organization
        result = self._executor.execute(
            classification_output=classification_output,
            target_dir=target_dir,
            root_dir=root_dir,
            dry_run=dry_run,
            create_restoration_point=create_restoration_point,
            manifest_path=manifest_path,
        )

        # Log summary
        self._log_result_summary(result)

        return result

    def preview_organization(
        self,
        classification_output: Any,
        target_dir: str,
        root_dir: str,
    ) -> ExecutionResult:
        """
        Preview file organization without executing.

        Convenience method that runs organize_files in dry-run mode.

        Args:
            classification_output: Output from Task3 LLM classifier
            target_dir: Target directory for organized files
            root_dir: Original directory where files were scanned

        Returns:
            ExecutionResult showing what would happen (all operations marked as success)
        """
        logger.info("Previewing file organization (dry-run mode)")
        return self.organize_files(
            classification_output=classification_output,
            target_dir=target_dir,
            root_dir=root_dir,
            dry_run=True,
            create_restoration_point=False,
        )

    @staticmethod
    def _validate_inputs(
        classification_output: Any,
        target_dir: str,
        root_dir: str,
    ) -> None:
        """
        Validate inputs for file organization.

        Args:
            classification_output: Must have path_mappings attribute
            target_dir: Must be a valid directory path
            root_dir: Must be a valid directory path

        Raises:
            ValueError: If any input is invalid
        """
        # Validate classification output
        if not hasattr(classification_output, "path_mappings"):
            raise ValueError("classification_output must have 'path_mappings' attribute")

        path_mappings = classification_output.path_mappings
        if not isinstance(path_mappings, dict):
            raise ValueError("path_mappings must be a dictionary")

        if len(path_mappings) == 0:
            raise ValueError("path_mappings is empty - no files to organize")

        # Validate target_dir
        target_dir_path = Path(target_dir)
        if target_dir_path.exists() and not target_dir_path.is_dir():
            raise ValueError(f"target_dir exists but is not a directory: {target_dir}")

        # Validate root_dir
        root_dir_path = Path(root_dir)
        if not root_dir_path.exists():
            logger.warning(f"root_dir does not exist: {root_dir} (this may be intentional)")

        logger.debug(f"Input validation passed: {len(path_mappings)} files to organize")

    @staticmethod
    def _log_result_summary(result: ExecutionResult) -> None:
        """
        Log detailed summary of execution result.

        Args:
            result: ExecutionResult to summarize
        """
        logger.info("=" * 60)
        logger.info("File Organization Summary")
        logger.info("=" * 60)
        logger.info(f"Total files:      {result.total_count}")
        logger.info(f"Successfully moved: {result.success_count}")
        logger.info(f"Failed:           {result.failed_count}")
        logger.info(f"Skipped:          {result.skipped_count}")
        logger.info(f"Execution time:   {result.execution_time:.2f}s")

        if result.restoration_manifest_path:
            logger.info(f"Restoration manifest: {result.restoration_manifest_path}")
        else:
            logger.info("No restoration manifest created")

        # Log failed operations
        if result.failed_count > 0:
            logger.warning(f"{result.failed_count} operations failed:")
            for op in result.operations:
                if op.status == "failed":
                    logger.warning(f"  - {op.old_path}: {op.error}")

        # Log skipped operations
        if result.skipped_count > 0:
            logger.info(f"{result.skipped_count} operations skipped:")
            for op in result.operations:
                if op.status == "skipped":
                    logger.info(f"  - {op.old_path}: {op.error}")

        logger.info("=" * 60)
