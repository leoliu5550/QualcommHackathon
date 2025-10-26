from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class ScanOutput:
    """The output of scanning the root directory"""

    path: str
    name: str
    size: int


@dataclass
class ReportOutput:
    """The generated report after scanning the root directory"""

    root: str
    file_count: int
    total_size: int
    files: List[ScanOutput]


class IFileScanner(ABC):
    @abstractmethod
    def scan(self) -> ScanOutput:
        pass

    @abstractmethod
    def generate_report(self) -> ReportOutput:
        pass

    @abstractmethod
    def save_report(self) -> None:
        pass
