from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class FilePathEntry:
    initial_path: str
    original: str
    new: str


@dataclass
class ClassificationReport:
    timestamp: str
    file_paths: List[FilePathEntry]


class ClassificationReportHtmlPort(ABC):
    """
    Port: Domain-level interface for generating HTML from a classification report.
    """

    @abstractmethod
    def generate_html(self, report: ClassificationReport, root_dir: Path) -> Path:
        """Generate an HTML report and return the output file path."""
        pass

    @abstractmethod
    def load_report_from_json(self, json_path: Path) -> ClassificationReport:
        """
        Load a classification report from a JSON file and convert it into dataclasses.

        Args:
            json_path (Path): Path to the JSON file containing the classification report.

        Returns:
            ClassificationReport: A dataclass instance representing the report.
        """
        pass

    @abstractmethod
    def load_report_from_dict(self, data: dict) -> ClassificationReport:
        """
        Convert a dictionary into a ClassificationReport dataclass instance.

        Args:
            data (dict): Dictionary containing 'timestamp' and 'file_paths' keys.
                        'file_paths' should be a list of dictionaries with keys
                        'initial_path', 'original', and 'new'.

        Returns:
            ClassificationReport: A dataclass instance representing the report.
        """
        pass
