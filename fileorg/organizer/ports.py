"""
Organizer module - Data contracts and interface definitions.

This module defines the unified data structures for file organization
and restoration, combining execution tracking with backup mechanisms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class OperationStatus:
    """
    Execution status for a single file operation.

    Records the result of attempting to move a single file during organization.

    Usage:
        Created during file organization to track individual file movement results.

    Example:
        ```python
        status = OperationStatus(
            old_path="C:/Users/user/Documents/report.pdf",
            new_path="C:/Users/user/Documents/Organized/Financial/report.pdf",
            status="success",
            error=None,
            category="Financial"
        )
        ```

    Args:
        old_path: Original absolute file path
        new_path: Target absolute file path
        status: Execution status ("success", "failed", or "skipped")
        error: Error message if failed, None if successful
        category: File classification category
    """

    old_path: str
    new_path: str
    status: str
    error: Optional[str]
    category: str


@dataclass
class ExecutionResult:
    """
    Complete summary of file organization execution.

    Aggregates results from all file operations with statistics and backup information.

    Usage:
        Returned by organizer after executing operations, used for logging and display.

    Example:
        ```python
        result = ExecutionResult(
            total_count=10,
            success_count=8,
            failed_count=1,
            skipped_count=1,
            operations=[status1, status2, ...],
            backup_dir="C:/Users/user/Documents/.backup",
            execution_time=2.5
        )
        ```

    Args:
        total_count: Total number of planned file operations
        success_count: Number of successfully moved files
        failed_count: Number of failed file operations
        skipped_count: Number of skipped operations
        operations: Detailed status for each file operation
        backup_dir: Path to the .backup directory containing file_paths.json
        execution_time: Total execution time in seconds
    """

    total_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    operations: List[OperationStatus]
    backup_dir: str
    execution_time: float


@dataclass
class FilePathRecord:
    """
    Single file path record with three stages of tracking.

    Records a single file's path at three stages: initial, original, and new.

    Args:
        initial_path: Original file path when first organized (permanent baseline)
        original: Latest scan path before current operation (for restoration)
        new: Target path after LLM classification (for execution)
    """

    initial_path: str
    original: str
    new: str


@dataclass
class FilePathBackup:
    """
    Backup data structure for file path tracking.

    Records file paths at three stages for all files.
    Enables complete restoration even if users manually move files after organization.

    Usage:
        Created during file organization and persisted to .backup/file_paths.json.

    Example:
        ```python
        backup = FilePathBackup(
            timestamp="2025-11-14T11:14:30",
            file_paths=[
                FilePathRecord(
                    initial_path="C:/Users/user/Documents/report.pdf",
                    original="C:/Users/user/Documents/report.pdf",
                    new="C:/Users/user/Documents/Organized/Financial/report.pdf"
                )
            ]
        )
        ```

    Args:
        timestamp: ISO 8601 timestamp of backup creation
        file_paths: List of file path records, one per file
    """

    timestamp: str
    file_paths: List[FilePathRecord]


class IFileOrganizer(ABC):
    """
    Interface for unified file organization and restoration operations.

    Defines the contract for implementing complete file organization lifecycle:
    execution with backup creation and restoration capabilities.

    Usage:
        Implement this interface to provide different storage strategies
        (local filesystem, cloud storage, etc.).
    """

    @abstractmethod
    def execute(
        self,
        classification_output: Any,  # ClassificationOutput from llm_classifier
        root_dir: str,
        dry_run: bool = False,
    ) -> ExecutionResult:
        """
        Execute file organization based on classification results.

        Creates .backup directory, saves file_paths.json, moves files to organized
        locations, and cleans up empty directories.

        Args:
            classification_output: Output from LLM classifier containing
                path_mappings (Dict[str, FileMapping])
            root_dir: Root directory where files should be organized
                (e.g., "C:/Users/USER/Documents")
            dry_run: If True, simulate operations without actual file movement

        Returns:
            ExecutionResult with statistics and detailed operation status

        Raises:
            ValueError: If classification_output is invalid
            IOError: If unable to access root directory

        Note:
            This method performs:
            1. Create .backup directory at root_dir/.backup
            2. Generate and save file_paths.json
            3. Execute file movements to organized locations
            4. Clean up empty directories created by moves
        """
        pass

    @abstractmethod
    def restore(
        self,
        root_dir: str,
    ) -> Dict[str, Any]:
        """
        Restore files to their original locations.

        Reads .backup/file_paths.json, locates files (even if manually moved),
        and restores them to initial_path locations. Cleans up empty directories.

        Args:
            root_dir: Root directory containing .backup folder
                (e.g., "C:/Users/USER/Documents")

        Returns:
            Dictionary with restoration results:
                {
                    "total": int,           # Total files to restore
                    "restored": int,        # Successfully restored
                    "failed": int,          # Failed restorations
                    "skipped": int,         # Skipped (not found)
                    "errors": List[str]     # Error messages
                }

        Raises:
            FileNotFoundError: If .backup/file_paths.json doesn't exist
            ValueError: If backup data is corrupted

        Note:
            This method can restore files even if users manually moved them
            after organization, by searching for files and matching them to
            the backup records.
        """
        pass
