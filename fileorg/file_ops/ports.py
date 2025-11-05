from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ScanOutput:
    """
    Represents a single file or directory discovered during the scan.

    Attributes:
        path (str): Absolute or relative path of the scanned file.
        name (str): File name (basename) extracted from the path.
        size (int): File size in bytes.
    """

    path: str
    name: str
    size: int


@dataclass
class ReportOutput:
    """
    Represents the overall result of a directory scan.

    This report aggregates information about all files under the root
    directory, including total size and file count.

    Attributes:
        root (str): The root directory that was scanned.
        file_count (int): Total number of files found in the directory tree.
        total_size (int): Cumulative size (in bytes) of all scanned files.
        files (List[ScanOutput]): List of detailed scan results for each file.
    """

    root: str
    file_count: int
    total_size: int
    files: List[ScanOutput]


class IFileScanner(ABC):
    """
    Interface for file system scanning and report generation.

    This abstract base class defines the required methods for
    implementing a file scanner that can traverse directories,
    collect file information, and produce a summary report.
    """

    @abstractmethod
    def __init__(self, root_dir: str, ignore_patterns: Optional[List[str]] = None):
        """
        Initializes the file scanner.

        Args:
            root_dir (str): The path to the directory that will be scanned.
            ignore_patterns (Optional[List[str]]): Custom ignore patterns
                to exclude files or directories during scanning.
        """
        pass

    @abstractmethod
    def scan(self) -> ScanOutput:
        """
        Scans the root directory or a specified path to collect file information.

        Returns:
            ScanOutput: Metadata of a single scanned file or directory entry.

        Raises:
            FileNotFoundError: If the specified directory does not exist.
            PermissionError: If access to certain files or directories is denied.
        """
        pass

    @abstractmethod
    def generate_report(self) -> ReportOutput:
        """
        Aggregates scan results into a summary report.

        Returns:
            ReportOutput: A report summarizing total files, sizes,
            and other relevant statistics from the scan results.
        """
        pass

    @abstractmethod
    def save_report(self) -> None:
        """
        Persists the generated report to a file (e.g., JSON, CSV, or text format).

        Raises:
            IOError: If the report file cannot be written.
        """
        pass
