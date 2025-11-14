"""
Restoration module for AI Filing System.

This module provides file operation restoration (rollback) functionality.
It creates restoration points before file organization and enables reverting
file movements back to their original locations.
"""

from fileorg.restoration.ports import (
    FileOperation,
    IRestorationManager,
    RestorationPoint,
)

__all__ = [
    "FileOperation",
    "RestorationPoint",
    "IRestorationManager",
]
