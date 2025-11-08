"""
FileOrg File Scanner Module

This module provides intelligent file system scanning capabilities that form
the foundation of our organization pipeline. We've designed it to be respectful
of system resources while being comprehensive in scope.

Our scanning approach balances thoroughness with performance, automatically
skipping irrelevant system files while capturing everything users care about.
"""

import fnmatch
import json
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from fileorg.file_ops.ports import IFileScanner, ReportOutput, ScanOutput


class FileScanner(IFileScanner):
    """A class for intelligent and efficient file system scanning.

    The FileScanner class provides recursive directory scanning functionality
    that skips common irrelevant system files while capturing essential file data.
    It can generate detailed reports including file statistics and total size.

    Attributes:
        root_dir (Path): The root directory to scan.
        ignore_patterns (List[str]): Glob-style ignore patterns.
    """

    DEFAULT_IGNORE_PATTERNS = [
        ".*",  # 隱藏檔案與資料夾
        "__pycache__",
        "node_modules",
        "*.tmp",
        "*.log",
        "*.bak",
        "Thumbs.db",
        ".DS_Store",
    ]

    def __init__(self, root_dir: str, ignore_patterns: Optional[List[str]] = None):
        """Initialize the FileScanner instance.

        Args:
            root_dir (str): The path to the directory to be scanned.
            ignore_patterns (Optional[List[str]]): Custom ignore patterns.
        """
        self.root_dir = Path(root_dir).resolve()
        self.ignore_patterns = ignore_patterns or self.DEFAULT_IGNORE_PATTERNS

        if not self.root_dir.exists():
            logger.error(f"Directory does not exist: {self.root_dir}")
            raise FileNotFoundError(f"Directory does not exist: {self.root_dir}")
        if not self.root_dir.is_dir():
            logger.error(f"Path is not a directory: {self.root_dir}")
            raise NotADirectoryError(f"Path is not a directory: {self.root_dir}")

    def _is_ignored(self, path: Path) -> bool:
        """Check whether the given file or directory should be ignored.

        Args:
            path (Path): The file or directory to check.

        Returns:
            bool: True if the path matches any ignore pattern, False otherwise.
        """
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path.name, pattern):
                return True
        return False

    def _get_file_info(self, entry: Path) -> Optional[Dict[str, str]]:
        """Get file metadata, return None if unreadable."""
        try:
            return {
                "path": str(entry.resolve()),
                "name": entry.name,
                "size": int(entry.stat().st_size),
            }
        except OSError:
            return None

    def _scan(self, directory: Path) -> List[Dict[str, str]]:
        results = []
        for entry in directory.iterdir():
            if self._is_ignored(entry):
                continue
            if entry.is_dir():
                results.extend(self._scan(entry))
            elif entry.is_file():
                file_info = self._get_file_info(entry)
                if file_info:
                    results.append(file_info)
        return results

    def scan(self) -> ScanOutput:
        """Perform a complete scan starting from the root directory.

        Returns:
            List[Dict[str, str]]: List of scanned file information.
        """
        return self._scan(self.root_dir)

    def generate_report(self) -> ReportOutput:
        """Generate a detailed scan report for the target directory.

        Returns:
            Dict[str, object]: Report containing:
                - "root" (str): Root directory path
                - "file_count" (int): Total number of files scanned
                - "total_size" (int): Total file size in bytes
                - "files" (List[Dict]): Detailed file list (path, name, size)
        """
        files = self.scan()
        total_size = sum(int(f["size"]) for f in files)
        report = {
            "root": str(self.root_dir),
            "file_count": len(files),
            "total_size": total_size,
            "files": files,
        }
        return report

    def save_report(self, output_path: str) -> None:
        """Save the scan report as a JSON file.

        Args:
            output_path (str): Path to the JSON file to write.
        """
        report = self.generate_report()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)


def main():
    """Example command-line entry point."""
    # target_dir = input("Enter directory path to scan: ").strip()
    target_dir = "/Users/leoliu/Documents/Sinfo"
    scanner = FileScanner(target_dir)
    report = scanner.generate_report()

    logger.debug("\n=== File Scan Report ===")
    logger.debug(f"Root Directory: {report['root']}")
    logger.debug(f"Total Files: {report['file_count']}")
    logger.debug(f"Total Size: {report['total_size']} bytes")

    output_file = "scan_report.json"
    scanner.save_report(output_file)
    logger.debug(f"\nReport saved to {output_file}")


if __name__ == "__main__":
    main()
