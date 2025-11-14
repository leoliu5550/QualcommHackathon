"""
File organization use case - Business logic orchestration.

This module coordinates file organization and restoration operations,
serving as the application layer interface for the organizer module.
"""

from typing import Any, Dict

from fileorg.organizer.ports import ExecutionResult, IFileOrganizer


class FileOrganizerUseCase:
    """
    Use case for file organization and restoration operations.

    Orchestrates file organization workflow by delegating to the
    file organizer implementation.

    Usage:
        ```python
        from fileorg.organizer.adapters.local_executor import LocalFileOrganizer

        organizer = LocalFileOrganizer()
        use_case = FileOrganizerUseCase(organizer)

        # Organize files
        result = use_case.organize_files(classification_output, "C:/Users/user/Documents")

        # Restore files
        restore_result = use_case.restore_files("C:/Users/user/Documents")
        ```
    """

    def __init__(self, organizer: IFileOrganizer):
        """
        Initialize use case with organizer implementation.

        Args:
            organizer: File organizer implementation (e.g., LocalFileOrganizer)
        """
        self._organizer = organizer

    def organize_files(
        self,
        classification_output: Any,
        root_dir: str,
        dry_run: bool = False,
    ) -> ExecutionResult:
        """
        Organize files based on classification results.

        Creates backup, moves files to organized locations, and cleans up
        empty directories.

        Args:
            classification_output: Output from LLM classifier with path_mappings
            root_dir: Root directory for file organization
            dry_run: If True, preview operations without execution

        Returns:
            ExecutionResult with operation statistics and details

        Raises:
            ValueError: If classification_output is invalid
            IOError: If unable to access root directory
        """
        return self._organizer.execute(
            classification_output=classification_output,
            root_dir=root_dir,
            dry_run=dry_run,
        )

    def restore_files(self, root_dir: str) -> Dict[str, Any]:
        """
        Restore files to their original locations.

        Reads backup from .backup/file_paths.json and restores all files
        to their initial locations.

        Args:
            root_dir: Root directory containing .backup folder

        Returns:
            Dictionary with restoration statistics:
                {
                    "total": int,
                    "restored": int,
                    "failed": int,
                    "skipped": int,
                    "errors": List[str]
                }

        Raises:
            FileNotFoundError: If .backup/file_paths.json doesn't exist
            ValueError: If backup data is corrupted
        """
        return self._organizer.restore(root_dir=root_dir)
