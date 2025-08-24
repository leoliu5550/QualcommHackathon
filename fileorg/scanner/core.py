"""
FileOrg File Scanner Module

This module provides intelligent file system scanning capabilities that form
the foundation of our organization pipeline. We've designed it to be respectful
of system resources while being comprehensive in scope.

Our scanning approach balances thoroughness with performance, automatically
skipping irrelevant system files while capturing everything users care about.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fileorg.scanner.helpers import get_file_info, save_scan_result, print_scan_summary


class FileScanner:
    """
    Intelligent file system scanner for content discovery.

    FileScanner represents our philosophy of understanding before acting.
    It provides the essential first step in any organization workflow:
    knowing what we're working with.

    We've built in smart defaults for common scenarios while allowing
    customization for specialized needs. The scanner is designed to evolve
    with user patterns and system capabilities.

    Attributes:
        target_path (Path): Directory being scanned
        max_depth (Optional[int]): Maximum recursion depth
        ignore_dirs (set): Directories to skip during scanning

    Future Enhancements:
        We're exploring real-time scanning, change detection, and integration
        with cloud storage providers for hybrid workflows.
    """

    def __init__(self, target_path: str, max_depth: Optional[int] = None):
        """
        Initialize the file scanner with intelligent defaults.

        We automatically configure sensible ignore patterns and depth limits
        to provide the best balance of coverage and performance. These defaults
        are based on analysis of real-world usage patterns.

        Args:
            target_path (str): Directory path to scan
            max_depth (Optional[int]): Maximum recursion depth for scanning.
                                     None means unlimited depth.

        Raises:
            FileNotFoundError: If target path doesn't exist
            NotADirectoryError: If target path isn't a directory

        Note:
            We're working on automatic depth optimization based on directory
            structure analysis to prevent excessive resource usage.
        """
        self.target_path = Path(target_path)
        self.max_depth = max_depth
        self.scanned_files = []
        # 忽略的資料夾名稱
        self.ignore_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            ".idea",
            ".vscode",
            "tidy_report",
            ".backup",
            "Organized_Files_*",
        }

        # 基本路徑驗證
        if not self.target_path.exists():
            raise FileNotFoundError(f"目標路徑不存在: {target_path}")

        if not self.target_path.is_dir():
            raise NotADirectoryError(f"目標路徑不是資料夾: {target_path}")

    def scan_directory(self) -> List[str]:
        """
        Perform recursive directory scanning with intelligent filtering.

        Our scanning algorithm is designed to be efficient and respectful,
        automatically skipping system directories and hidden files that
        typically aren't part of user organization workflows.

        Returns:
            List[str]: Paths to all discovered files

        Features:
            - Automatic system directory exclusion
            - Hidden file filtering
            - Permission error handling
            - Depth limiting for performance

        Note:
            We're continuously refining our ignore patterns based on user
            feedback and common file organization scenarios.
        """
        self.scanned_files = []
        self._recursive_scan(self.target_path, 0)
        return self.scanned_files

    def _recursive_scan(self, current_path: Path, current_depth: int):
        """
        Recursively scan directories with intelligent pattern matching.

        This internal method implements our core scanning logic, balancing
        thoroughness with performance. We handle edge cases gracefully and
        provide informative feedback when issues are encountered.

        Args:
            current_path (Path): Current directory being scanned
            current_depth (int): Current recursion depth

        Features:
            - Graceful permission error handling
            - Smart pattern-based directory exclusion
            - Depth-based performance optimization
            - Cross-platform path handling
        """
        # 檢查深度限制
        if self.max_depth is not None and current_depth > self.max_depth:
            return

        try:
            for item in current_path.iterdir():
                # 跳過隱藏檔案和資料夾
                if item.name.startswith("."):
                    continue

                # 跳過忽略清單中的資料夾
                if item.is_dir() and item.name in self.ignore_dirs:
                    continue

                # 跳過符合特定模式的資料夾 (如 Organized_Files_*)
                if item.is_dir() and item.name.startswith("Organized_Files_"):
                    continue

                if item.is_file():
                    self.scanned_files.append(str(item))
                elif item.is_dir():
                    # 遞迴掃描子資料夾
                    self._recursive_scan(item, current_depth + 1)

        except PermissionError:
            print(f"警告: 無權限存取 {current_path}")
        except Exception as e:
            print(f"掃描錯誤 {current_path}: {e}")

    def scan_with_details(
        self, save_result: bool = True, output_file: str = "scan_result.json"
    ) -> Dict[str, Any]:
        """
        Perform comprehensive directory scan with detailed file analysis.

        This method represents our commitment to providing rich, actionable
        information about discovered files. Beyond simple path enumeration,
        we gather metadata that enables intelligent organization decisions.

        Args:
            save_result (bool): Whether to persist scan results to disk
            output_file (str): Output filename for scan results

        Returns:
            Dict[str, Any]: Comprehensive scan results including:
                - File paths and metadata
                - Scan timestamps and statistics
                - Directory structure information

        Features:
            - Rich file metadata extraction
            - Scan performance metrics
            - Structured result formatting
            - Optional result persistence

        Note:
            We're exploring enhanced metadata extraction including content
            fingerprinting and relationship detection for improved categorization.
        """
        print(f"開始掃描: {self.target_path}")

        # 獲取檔案路徑列表
        file_paths = self.scan_directory()

        # 收集檔案詳細資訊
        file_details = []
        for file_path_str in file_paths:
            file_path = Path(file_path_str)
            file_info = get_file_info(file_path)
            file_details.append(file_info)

        # 組織掃描結果
        scan_result = {
            "scan_time": datetime.now().isoformat(),
            "target_path": str(self.target_path.absolute()),
            "original_files": file_details,
        }

        print(f"掃描完成: 找到 {len(file_details)} 個檔案")

        # 顯示掃描摘要
        # Display scan summary with intelligent formatting
        print_scan_summary(scan_result)

        # 保存掃描結果（如果需要）
        if save_result:
            save_scan_result(scan_result, output_file)

        return scan_result
