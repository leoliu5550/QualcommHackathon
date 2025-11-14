"""
File Organizer module - Data contracts and interface definitions.

This module defines the core data structures and interfaces for file
organization execution, responsible for moving files according to
classification results and integrating with the restoration mechanism.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class OperationStatus:
    """
    Execution status for a single file operation.

    Records the result of attempting to move a single file, including
    success/failure status and any error information.

    Usage:
        Created during file organization execution to track individual
        file movement results.

    Example:
        ```python
        status = OperationStatus(
            old_path="C:/Users/user/Documents/report.pdf",
            new_path="C:/Users/user/Organized/Financial_Reports/report.pdf",
            status="success",
            error=None,
            category="Financial Reports"
        )
        ```
    """

    old_path: str
    """Original absolute file path (must match FileMapping.old_path from Task3)."""

    new_path: str
    """Target absolute file path (target_dir / new_relative_path)."""

    status: str
    """Execution status: "success", "failed", or "skipped"."""

    error: Optional[str]
    """Error message if failed, None if successful."""

    category: str
    """File classification category (from FileMapping.category)."""


@dataclass
class ExecutionResult:
    """
    Complete summary of file organization execution.

    Aggregates results from all file operations, providing statistics
    and detailed status for each file movement.

    Usage:
        Returned by file organizer after executing all operations,
        used for logging, UI display, and verification.

    Example:
        ```python
        result = ExecutionResult(
            total_count=10,
            success_count=8,
            failed_count=1,
            skipped_count=1,
            operations=[status1, status2, ...],
            restoration_manifest_path="C:/restore.json",
            execution_time=2.5
        )
        ```
    """

    total_count: int
    """Total number of planned file operations."""

    success_count: int
    """Number of successfully moved files."""

    failed_count: int
    """Number of failed file operations."""

    skipped_count: int
    """Number of skipped file operations (e.g., source file not found)."""

    operations: List[OperationStatus]
    """Detailed status for each file operation."""

    restoration_manifest_path: Optional[str]
    """Path to the restoration manifest (if created)."""

    execution_time: float
    """Total execution time in seconds."""


class IFileExecutor(ABC):
    """
    Interface for file organization execution.

    Defines the contract for implementing file movement operations,
    including integration with the restoration mechanism (Task4).

    Usage:
        Implement this interface to provide different execution strategies
        (local filesystem, cloud storage, etc.).
    """

    @abstractmethod
    def execute(
        self,
        classification_output: Any,  # ClassificationOutput from Task3
        target_dir: str,
        root_dir: str,
        dry_run: bool = False,
        create_restoration_point: bool = True,
        manifest_path: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute file organization based on classification results.

        Moves files according to classification output, optionally creating
        a restoration point before execution.

        Args:
            classification_output: Output from Task3 LLM classifier containing
                path_mappings (Dict[str, FileMapping])
            target_dir: Target directory for organized files (absolute path)
            root_dir: Original directory where files were scanned (for restoration)
            dry_run: If True, simulate operations without actual file movement
            create_restoration_point: Whether to create restoration point before execution
            manifest_path: Path for restoration manifest (auto-generated if None)

        Returns:
            ExecutionResult with statistics and detailed operation status

        Raises:
            ValueError: If classification_output is invalid
            IOError: If unable to access target directory

        Note:
            When create_restoration_point is True, this method should:
            1. Create restoration point from classification_output
            2. Save restoration point to manifest
            3. Execute file operations
            4. Update restoration point with execution status
        """
        pass

    @abstractmethod
    def move_file(
        self,
        old_path: str,
        new_path: str,
        handle_conflict: bool = True,
    ) -> tuple[bool, Optional[str], str]:
        """
        Move a single file from old_path to new_path.

        Creates target directory if needed, handles filename conflicts,
        and provides detailed error reporting.

        Args:
            old_path: Source file path (absolute)
            new_path: Destination file path (absolute)
            handle_conflict: If True, rename on conflict; if False, fail on conflict

        Returns:
            Tuple of (success: bool, error: Optional[str], actual_new_path: str)
            - success: True if file moved successfully
            - error: Error message if failed, None if successful
            - actual_new_path: Final path (may differ from new_path if conflict resolved)

        Note:
            Conflict handling strategy: append _1, _2, etc. to filename
            Example: report.pdf -> report_1.pdf -> report_2.pdf
        """
        pass

    @abstractmethod
    def create_target_directory(
        self,
        path: str,
    ) -> bool:
        """
        Create target directory if it doesn't exist.

        Creates all parent directories as needed.

        Args:
            path: Directory path to create (absolute)

        Returns:
            True if directory was created or already exists, False on error

        Note:
            Should be safe to call multiple times (idempotent).
        """
        pass
