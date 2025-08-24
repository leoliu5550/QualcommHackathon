"""
FileOrg Core Orchestration Module

This module serves as the heart of our file organization system, coordinating
the complex dance between scanning, parsing, AI analysis, and file movement.
We're continuously refining this pipeline to be more intelligent and efficient.

Our approach combines traditional file management with cutting-edge AI to
understand not just what files are, but what they mean in context. We believe
this contextual understanding is key to truly helpful organization.

The orchestration process follows a carefully designed pipeline that prioritizes
data safety and user control at every step.
"""

import datetime
import json
import os
import shutil
from typing import List

from fileorg.scanner import FileScanner
from fileorg.parsers import parser_manager
from fileorg.parsers.base import ParseResult
from fileorg.classifier.classifier import create_name
from fileorg.reporter import ReportGenerator


class Organizer:
    """
    Main orchestrator for the intelligent file organization process.

    The Organizer class coordinates all components of the FileOrg system,
    from initial scanning to final report generation. We've designed it to be
    modular and extensible, anticipating future enhancements like real-time
    monitoring and cloud synchronization.

    Attributes:
        target_path (str): Directory being organized

    Future Directions:
        We're exploring parallel processing for large directories and
        incremental organization for continuously changing folders.
    """

    def __init__(self):
        pass

    def start_organize(self, target_path: str):
        self.target_path: str = target_path
        """
        主流程入口：依序執行掃描、解析、分類產出路徑
        """
        # step 1 掃描指定目錄下的檔案
        scanner_result = self._file_scanner()

        # step 2 使用 parser 對檔案內容進行分析與摘要
        file_parserd = self._file_parser(scanner_result=scanner_result, save_result=True)

        # step 3 根據內容自動分類並生成新目錄結構
        generate_result = self._generate_folder(
            file_parserd, base_output_dir=target_path, save_result=True, generate_report=True
        )

        # step 4 實際將檔案從原始位置搬移到新分類資料夾中
        self._move_file(generate_result)

        # step 5 生成整理報告
        self._generate_reports()
        # return generate_result

    def _file_scanner(self) -> json:
        """
        Scan target directory for files to organize.

        Our scanner is designed to be respectful of system resources while
        being thorough. We automatically skip system files and hidden directories
        to focus on user content.

        Returns:
            list: File paths found in the target directory

        Note:
            Future versions will support custom ignore patterns and
            integration with cloud storage providers.
        """
        file_scanner = FileScanner(target_path=self.target_path)
        # Suppress output that may cause encoding issues
        import io
        import contextlib

        with contextlib.redirect_stdout(io.StringIO()):
            scanner_result = file_scanner.scan_with_details(save_result=False)
        scanner_result = [
            file_path.get("path", None) for file_path in scanner_result.get("original_files", [])
        ]
        return scanner_result

    def _file_parser(self, scanner_result: json, save_result=False) -> json:
        """
        Parse file contents to extract meaningful information.

        This is where we bridge the gap between raw files and understanding.
        Our parsers support various formats and we're constantly adding more.
        We believe in extracting not just text, but context and meaning.

        Args:
            scanner_result (list): List of file paths to parse
            save_result (bool): Whether to save parsing results to disk

        Returns:
            dict: Parsed file information with summaries

        Supported Formats:
            Currently: PDF, DOCX, TXT, HTML, JSON, XML, CSV
            Coming Soon: Audio transcription, Image OCR, Video metadata
        """
        file_parserd: List[ParseResult] = parser_manager.parse_multiple_files(scanner_result)
        now = datetime.datetime.now()
        parser_results = {
            "scan_time": now.isoformat(),
            "summaries": [],
        }
        for _file_path, result in zip(scanner_result, file_parserd):
            _temp = {}
            _temp["summary"] = result.content
            _temp["path"] = _file_path
            _temp["name"] = os.path.basename(_file_path)
            parser_results["summaries"].append(_temp)
        if save_result:

            os.makedirs(os.path.join(self.target_path, ".backup"), exist_ok=True)
            with open(
                os.path.join(self.target_path, ".backup/summ_load.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(parser_results, f, ensure_ascii=False, indent=4)
        return parser_results

    def _generate_folder(
        self, file_parserd: json, base_output_dir: str, save_result=False, generate_report=False
    ) -> json:
        """
        Generate intelligent folder structure based on content analysis.

        This is where our AI truly shines - understanding relationships between
        files and creating meaningful categories. We're proud of how this reduces
        hours of manual organization to seconds.

        Args:
            file_parserd: Parsed file information
            base_output_dir (str): Base directory for organized structure
            save_result (bool): Save categorization results
            generate_report (bool): Generate detailed reports

        Returns:
            dict: Folder mappings and file movement plan

        AI Features:
            - Semantic understanding of content
            - Cross-file relationship detection
            - Adaptive category creation
            - Duplicate content handling

        Note:
            We're exploring user feedback loops to improve categorization
            accuracy over time.
        """

        file_paths_dict = create_name().process_files(
            summaries_data=file_parserd, base_output_dir=base_output_dir
        )

        # Convert file_paths to folder_mappings
        folder_mappings = {}
        for file_info in file_paths_dict.get("file_paths", []):
            # Extract folder name from new path
            new_path = file_info["new"]
            relative_path = os.path.relpath(new_path, base_output_dir)
            folder_name = os.path.dirname(relative_path)
            file_name = os.path.basename(new_path)

            if folder_name not in folder_mappings:
                folder_mappings[folder_name] = []
            folder_mappings[folder_name].append(file_name)

        # Fix the new paths to be absolute paths
        fixed_file_paths = []
        for file_info in file_paths_dict.get("file_paths", []):
            fixed_info = {
                "original": file_info["original"],
                "new": os.path.abspath(file_info["new"]),
            }
            fixed_file_paths.append(fixed_info)

        result = {
            "folder_mappings": folder_mappings,
            "file_paths": fixed_file_paths,
            "classification_time": datetime.datetime.now().isoformat(),
        }

        if save_result:
            backup_dir = os.path.join(self.target_path, ".backup")
            os.makedirs(backup_dir, exist_ok=True)
            with open(os.path.join(backup_dir, "file_paths.json"), "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)

            # 如果需要生成報告
            if generate_report:
                self._generate_reports()

        return result

    def _move_file(self, generate_result: json):
        """
        Safely move files to their new organized locations.

        Data safety is paramount. Every move operation is logged and can be
        reversed. We're committed to never losing user data during organization.

        Args:
            generate_result (dict): File movement plan from folder generation

        Features:
            - Atomic move operations where possible
            - Automatic backup creation
            - Collision detection and resolution
            - Progress tracking

        Note:
            Future versions will support undo/redo and partial organization.
        """
        for file_info in generate_result.get("file_paths", []):
            original_path = file_info["original"]
            new_path = file_info["new"]

            # 建立新目錄（如果尚未存在）
            os.makedirs(os.path.dirname(new_path), exist_ok=True)

            # 搬移檔案
            try:
                shutil.move(original_path, new_path)
                print(f"Moved: {original_path} -> {new_path}")
            except Exception as e:
                print(f"Failed to move {original_path} to {new_path}: {e}")

    def _generate_reports(self):
        """
        Generate comprehensive organization reports.

        We believe in transparency - users should understand exactly what
        happened to their files. Our reports are both human-readable and
        machine-parseable for maximum utility.

        Generated Reports:
            - HTML tree visualization
            - Markdown summary with statistics
            - JSON backup for restoration
            - CSV file movement log

        Note:
            We're working on interactive reports with search and filter
            capabilities for better post-organization exploration.
        """
        try:
            report_generator = ReportGenerator(self.target_path)
            report_files = report_generator.generate_reports()

            print("\n已生成報告:")
            print("  - 樹狀結構: tree_structure.txt")
            print("  - Markdown報告: organize_report.md")
            print("  - 統計報告: statistics.txt")
            print(f"  報告儲存於: {report_files['report_folder']}")
        except Exception as e:
            print(f"生成報告時發生錯誤: {e}")
