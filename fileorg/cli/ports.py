from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


class ProgressPort(ABC):
    """Abstract interface (port) for reporting progress in tasks.

    This port defines the contract between the core use cases and any external
    progress display implementation, such as CLI, GUI, or logging adapters.

    Methods:
        update(message: str): Update the current progress message.
        done(): Indicate that the task is completed.
    """

    @abstractmethod
    def update(self, message: str):
        """Update the progress display with a new message.

        Args:
            message (str): The progress message to display.
        """
        pass

    @abstractmethod
    def done(self):
        """Mark the progress as complete and perform any finalization."""
        pass


@dataclass
class OrganizeArgs:
    """Data class for 'organize' command arguments."""

    path: Path
    preview: bool
    model: str
    char_limit: int


@dataclass
class RestoreArgs:
    """Data class for 'restore' command arguments."""

    path: Path
