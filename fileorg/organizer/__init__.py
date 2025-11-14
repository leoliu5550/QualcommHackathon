"""
Organizer module - Unified file organization and restoration system.

This module integrates file execution and restoration functionality,
providing complete file organization lifecycle management.
"""

from fileorg.organizer.ports import (
    ExecutionResult,
    FilePathBackup,
    FilePathRecord,
    IFileOrganizer,
    OperationStatus,
)

__all__ = [
    "ExecutionResult",
    "FilePathBackup",
    "FilePathRecord",
    "IFileOrganizer",
    "OperationStatus",
]
