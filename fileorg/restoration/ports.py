"""
Restoration module - Data contracts and interface definitions.

This module defines the core data structures and interfaces for the file
restoration mechanism, enabling rollback of file organization operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class FileOperation:
    """
    Record of a single file movement operation.

    Represents one file's movement from its original location to a new organized
    location. Used for tracking operations and enabling restoration (rollback).

    Usage:
        Create when planning file organization, update status after execution.

    Example:
        ```python
        op = FileOperation(
            old_path="C:/Users/user/Documents/report.pdf",
            new_path="C:/Users/user/Organized/Financial_Reports/report.pdf",
            category="Financial Reports"
        )
        # After execution
        op.executed = True
        ```
    """

    old_path: str
    """Original absolute file path (must align with FileMapping.old_path from Task3)."""

    new_path: str
    """Target absolute file path (target_dir + new_relative_path)."""

    category: str
    """Classification category for this file."""

    executed: bool = False
    """Whether this operation has been executed."""

    error: Optional[str] = None
    """Error message if operation failed, None if successful."""


@dataclass
class RestorationPoint:
    """
    Complete snapshot of a file organization operation.

    Captures all information needed to restore files to their original state
    after a file organization operation. Persisted as JSON manifest.

    Usage:
        Create before file organization, save to manifest file, use to restore later.

    Example:
        ```python
        point = RestorationPoint(
            timestamp="2025-11-13T14:30:00",
            root_dir="C:/Users/user/Documents",
            target_dir="C:/Users/user/Organized",
            file_operations=[op1, op2, op3]
        )
        # Save to manifest
        manager.save_restoration_point(point, "path/to/manifest.json")
        ```
    """

    timestamp: str
    """ISO 8601 timestamp (serves as unique identifier)."""

    root_dir: str
    """Original scan root directory (where files were scanned from)."""

    target_dir: str
    """Target directory for file organization."""

    file_operations: List[FileOperation]
    """All planned file operations."""

    metadata: Optional[Dict[str, Any]] = None
    """Additional information (statistics, execution time, etc.)."""


class IRestorationManager(ABC):
    """
    Interface for restoration point management and file rollback operations.

    Defines the contract for creating, persisting, loading, and executing
    restoration of file organization operations.

    Usage:
        Implement this interface to provide different persistence mechanisms
        (JSON, database, etc.) for restoration points.
    """

    @abstractmethod
    def create_restoration_point(
        self,
        classification_output: Any,  # ClassificationOutput from Task3
        target_dir: str,
        root_dir: str,
        timestamp: Optional[str] = None,
    ) -> RestorationPoint:
        """
        Create a restoration point from classification results.

        Converts classification output into a restoration point with all
        file operations that will be executed.

        Args:
            classification_output: Output from Task3 LLM classifier containing
                path_mappings (Dict[str, FileMapping])
            target_dir: Target directory for organized files
            root_dir: Original directory where files were scanned
            timestamp: Optional ISO 8601 timestamp (auto-generated if None)

        Returns:
            RestorationPoint ready to be saved and used for restoration

        Raises:
            ValueError: If classification_output is invalid or missing required fields
        """
        pass

    @abstractmethod
    def save_restoration_point(
        self,
        restoration_point: RestorationPoint,
        manifest_path: str,
    ) -> None:
        """
        Persist restoration point to storage.

        Saves the restoration point (typically as JSON) to enable later restoration.
        Creates parent directories if they don't exist.

        Args:
            restoration_point: The restoration point to save
            manifest_path: Path where manifest should be saved (user-specified)

        Raises:
            IOError: If unable to write to manifest_path
            ValueError: If restoration_point is invalid
        """
        pass

    @abstractmethod
    def load_restoration_point(
        self,
        manifest_path: str,
    ) -> RestorationPoint:
        """
        Load restoration point from storage.

        Reads and deserializes a restoration point from its manifest file.

        Args:
            manifest_path: Path to the manifest file

        Returns:
            Loaded RestorationPoint

        Raises:
            FileNotFoundError: If manifest_path doesn't exist
            ValueError: If manifest is corrupted or invalid
        """
        pass

    @abstractmethod
    def restore(
        self,
        manifest_path: str,
    ) -> Dict[str, Any]:
        """
        Execute restoration (rollback) of file operations.

        Moves all files back to their original locations based on the
        restoration point manifest. Only restores executed operations.

        Args:
            manifest_path: Path to the restoration manifest

        Returns:
            Dictionary with restoration results:
                {
                    "total": int,           # Total operations
                    "restored": int,        # Successfully restored
                    "failed": int,          # Failed restorations
                    "skipped": int,         # Skipped (not executed)
                    "errors": List[str]     # Error messages
                }

        Raises:
            FileNotFoundError: If manifest_path doesn't exist
        """
        pass

    @abstractmethod
    def validate_restoration_point(
        self,
        restoration_point: RestorationPoint,
    ) -> bool:
        """
        Validate restoration point integrity.

        Checks that all paths are valid, accessible, and restoration is feasible.

        Args:
            restoration_point: The restoration point to validate

        Returns:
            True if valid and restorable, False otherwise
        """
        pass
