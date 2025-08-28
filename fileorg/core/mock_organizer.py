"""
FileOrg Mock Organizer Module

This module provides a mock version of the Organizer class for testing purposes.
It simulates all the functionality of the real organizer without actually moving
files or calling external dependencies, making it safe for testing workflows.

The mock maintains the same interface as the real organizer while providing
predictable, controllable outputs for testing scenarios.
"""

import datetime
import json
import os
import random
from typing import List, Dict, Any
from pathlib import Path


class MockOrganizer:
    """
    Mock version of the Organizer class for safe testing.
    
    This class simulates all the functionality of the real Organizer without:
    - Actually moving files
    - Calling external AI services
    - Creating real directories
    - Modifying the file system
    
    It provides realistic mock data that follows the same structure as the real system.
    """
    
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self.target_path = None
        self.mock_files = []
        self.mock_results = {}
        
        # Mock file types and their typical content summaries
        self.mock_file_types = {
            '.pdf': ['Research paper on machine learning', 'Financial report Q3 2024', 'User manual for software'],
            '.docx': ['Project proposal document', 'Meeting notes from team sync', 'Contract template'],
            '.txt': ['Configuration file', 'Log entries from system', 'Personal notes'],
            '.jpg': ['Photo from vacation', 'Screenshot of application', 'Diagram for presentation'],
            '.xlsx': ['Budget spreadsheet', 'Employee database', 'Sales report'],
            '.py': ['Python script for automation', 'Data analysis code', 'Web scraper implementation'],
            '.md': ['Project README file', 'Documentation notes', 'Technical specification'],
            '.json': ['Configuration settings', 'API response data', 'Database export'],
        }
        
        # Mock folder categories
        self.mock_categories = [
            'Documents/Work',
            'Documents/Personal',
            'Media/Photos',
            'Media/Screenshots', 
            'Development/Scripts',
            'Development/Projects',
            'Data/Spreadsheets',
            'Data/Reports',
            'Archive/Old_Files'
        ]

    def start_organize(self, target_path: str):
        """
        Mock version of the main organization workflow.
        
        Args:
            target_path (str): Directory to simulate organizing
        """
        self.target_path = target_path
        print(f"[MOCK] Starting organization of: {target_path}")
        
        # Simulate the full workflow
        print("[MOCK] Step 1: Scanning files...")
        scanner_result = self._file_scanner()
        
        print("[MOCK] Step 2: Parsing file contents...")
        file_parsed = self._file_parser(scanner_result=scanner_result, save_result=True)
        
        print("[MOCK] Step 3: Generating folder structure...")
        generate_result = self._generate_folder(
            file_parsed, 
            base_output_dir=target_path, 
            save_result=True, 
            generate_report=True
        )
        
        print("[MOCK] Step 4: Moving files (simulated)...")
        self._move_file(generate_result)
        
        print("[MOCK] Step 5: Generating reports...")
        self._generate_reports()
        
        print("[MOCK] Organization complete!")
        return generate_result

    def _file_scanner(self) -> List[str]:
        """
        Mock file scanner that generates realistic file paths.
        
        Returns:
            List[str]: Mock file paths
        """
        if not os.path.exists(self.target_path):
            print(f"[MOCK] Target path doesn't exist, generating mock files for: {self.target_path}")
        
        # Generate mock file list
        mock_files = []
        file_extensions = list(self.mock_file_types.keys())
        
        # Create a realistic mix of files
        for i in range(random.randint(15, 30)):  # Random number of files
            ext = random.choice(file_extensions)
            filename = f"mock_file_{i:02d}{ext}"
            file_path = os.path.join(self.target_path, filename)
            mock_files.append(file_path)
        
        # Add some files in subdirectories
        subdirs = ['temp', 'old', 'backup', 'misc']
        for subdir in subdirs:
            for i in range(random.randint(2, 5)):
                ext = random.choice(file_extensions)
                filename = f"{subdir}_file_{i}{ext}"
                file_path = os.path.join(self.target_path, subdir, filename)
                mock_files.append(file_path)
        
        self.mock_files = mock_files
        print(f"[MOCK] Found {len(mock_files)} files to organize")
        return mock_files

    def _file_parser(self, scanner_result: List[str], save_result: bool = False) -> Dict[str, Any]:
        """
        Mock file parser that generates realistic content summaries.
        
        Args:
            scanner_result (List[str]): List of file paths
            save_result (bool): Whether to save results
            
        Returns:
            Dict[str, Any]: Mock parsed results
        """
        now = datetime.datetime.now()
        parser_results = {
            "scan_time": now.isoformat(),
            "summaries": [],
        }
        
        for file_path in scanner_result:
            # Get file extension to determine mock content
            ext = os.path.splitext(file_path)[1].lower()
            if ext in self.mock_file_types:
                summary = random.choice(self.mock_file_types[ext])
            else:
                summary = f"Unknown file type: {ext}"
            
            file_info = {
                "summary": summary,
                "path": file_path,
                "name": os.path.basename(file_path)
            }
            parser_results["summaries"].append(file_info)
        
        if save_result:
            backup_dir = os.path.join(self.target_path, ".backup")
            print(f"[MOCK] Would save parsing results to: {backup_dir}/summ_load.json")
            # In real mode, we would create the directory and file here
            if not self.mock_mode:
                os.makedirs(backup_dir, exist_ok=True)
                with open(os.path.join(backup_dir, "summ_load.json"), "w", encoding="utf-8") as f:
                    json.dump(parser_results, f, ensure_ascii=False, indent=4)
        
        print(f"[MOCK] Parsed {len(parser_results['summaries'])} files")
        return parser_results

    def _generate_folder(
        self, 
        file_parsed: Dict[str, Any], 
        base_output_dir: str, 
        save_result: bool = False, 
        generate_report: bool = False
    ) -> Dict[str, Any]:
        """
        Mock folder generation that creates realistic categorization.
        
        Args:
            file_parsed: Parsed file information
            base_output_dir (str): Base directory for organization
            save_result (bool): Save categorization results
            generate_report (bool): Generate detailed reports
            
        Returns:
            Dict[str, Any]: Mock folder mappings and file paths
        """
        folder_mappings = {}
        file_paths = []
        
        for file_info in file_parsed.get("summaries", []):
            original_path = file_info["path"]
            filename = file_info["name"]
            
            # Mock categorization based on file extension and content
            ext = os.path.splitext(filename)[1].lower()
            category = self._mock_categorize_file(ext, file_info["summary"])
            
            # Create new path
            new_path = os.path.join(base_output_dir, category, filename)
            
            # Add to folder mappings
            if category not in folder_mappings:
                folder_mappings[category] = []
            folder_mappings[category].append(filename)
            
            # Add to file paths
            file_paths.append({
                "original": original_path,
                "new": os.path.abspath(new_path)
            })
        
        result = {
            "folder_mappings": folder_mappings,
            "file_paths": file_paths,
            "classification_time": datetime.datetime.now().isoformat(),
        }
        
        if save_result:
            backup_dir = os.path.join(self.target_path, ".backup")
            print(f"[MOCK] Would save classification results to: {backup_dir}/file_paths.json")
            if not self.mock_mode:
                os.makedirs(backup_dir, exist_ok=True)
                with open(os.path.join(backup_dir, "file_paths.json"), "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
        
        # Print categorization summary
        print(f"[MOCK] Categorized files into {len(folder_mappings)} folders:")
        for folder, files in folder_mappings.items():
            print(f"  - {folder}: {len(files)} files")
        
        return result

    def _mock_categorize_file(self, extension: str, summary: str) -> str:
        """
        Mock categorization logic based on file extension and content.
        
        Args:
            extension (str): File extension
            summary (str): File content summary
            
        Returns:
            str: Category folder path
        """
        # Simple rule-based categorization for testing
        if extension in ['.jpg', '.png', '.gif', '.bmp']:
            if 'screenshot' in summary.lower():
                return 'Media/Screenshots'
            else:
                return 'Media/Photos'
        elif extension in ['.py', '.js', '.html', '.css']:
            if 'script' in summary.lower():
                return 'Development/Scripts'
            else:
                return 'Development/Projects'
        elif extension in ['.xlsx', '.csv']:
            return 'Data/Spreadsheets'
        elif extension in ['.pdf', '.docx']:
            if 'report' in summary.lower():
                return 'Data/Reports'
            elif 'work' in summary.lower() or 'project' in summary.lower():
                return 'Documents/Work'
            else:
                return 'Documents/Personal'
        elif extension in ['.txt', '.md']:
            if 'config' in summary.lower() or 'log' in summary.lower():
                return 'Development/Config'
            else:
                return 'Documents/Personal'
        else:
            return 'Archive/Miscellaneous'

    def _move_file(self, generate_result: Dict[str, Any]):
        """
        Mock file moving that simulates the operation without actual file system changes.
        
        Args:
            generate_result (Dict[str, Any]): File movement plan
        """
        moved_count = 0
        failed_count = 0
        
        for file_info in generate_result.get("file_paths", []):
            if not isinstance(file_info, dict):
                print(f"[MOCK] Invalid file info format: {file_info}")
                failed_count += 1
                continue
            
            if "original" not in file_info or "new" not in file_info:
                print(f"[MOCK] Missing required keys in file info: {file_info}")
                failed_count += 1
                continue
            
            original_path = file_info["original"]
            new_path = file_info["new"]
            
            # Simulate successful move (with occasional "failures" for testing)
            if random.random() < 0.95:  # 95% success rate
                print(f"[MOCK] Would move: {os.path.basename(original_path)} -> {os.path.dirname(new_path)}")
                moved_count += 1
            else:
                print(f"[MOCK] Failed to move: {original_path}")
                failed_count += 1
        
        print(f"[MOCK] File movement summary: {moved_count} moved, {failed_count} failed")

    def _generate_reports(self):
        """
        Mock report generation that simulates creating organization reports.
        """
        report_files = {
            'tree_structure': os.path.join(self.target_path, '.reports', 'tree_structure.txt'),
            'markdown_report': os.path.join(self.target_path, '.reports', 'organize_report.md'),
            'statistics': os.path.join(self.target_path, '.reports', 'statistics.txt'),
            'report_folder': os.path.join(self.target_path, '.reports')
        }
        
        print("\n[MOCK] Generated reports:")
        print("  - 樹狀結構: tree_structure.txt")
        print("  - Markdown報告: organize_report.md") 
        print("  - 統計報告: statistics.txt")
        print(f"  報告儲存於: {report_files['report_folder']}")
        
        if not self.mock_mode:
            # In non-mock mode, actually create some basic report files
            os.makedirs(report_files['report_folder'], exist_ok=True)
            
            # Create a simple tree structure report
            with open(report_files['tree_structure'], 'w', encoding='utf-8') as f:
                f.write("Mock Organization Tree Structure\n")
                f.write("="*40 + "\n")
                for category in self.mock_categories:
                    f.write(f"{category}/\n")
                    f.write(f"  └── (mock files organized here)\n")

    def get_mock_status(self) -> Dict[str, Any]:
        """
        Get current mock status and results for testing.
        
        Returns:
            Dict[str, Any]: Mock status information
        """
        return {
            "mock_mode": self.mock_mode,
            "target_path": self.target_path,
            "mock_files_count": len(self.mock_files),
            "categories_used": len(self.mock_categories),
            "last_run": datetime.datetime.now().isoformat()
        }

    def set_mock_files(self, file_list: List[str]):
        """
        Set custom mock files for testing specific scenarios.
        
        Args:
            file_list (List[str]): List of mock file paths
        """
        self.mock_files = file_list
        print(f"[MOCK] Set {len(file_list)} custom mock files")

    def enable_real_mode(self):
        """Enable real file operations (use with caution in testing)"""
        self.mock_mode = False
        print("[WARNING] Mock mode disabled - real file operations enabled!")

    def enable_mock_mode(self):
        """Enable mock mode (safe for testing)"""
        self.mock_mode = True
        print("[MOCK] Mock mode enabled - safe testing mode")


# Convenience function for quick testing
def test_mock_organizer(test_path: str = "./test_directory"):
    """
    Quick test function to demonstrate mock organizer functionality.
    
    Args:
        test_path (str): Path to test directory
    """
    print("="*50)
    print("FileOrg Mock Organizer Test")
    print("="*50)
    
    organizer = MockOrganizer(mock_mode=True)
    
    try:
        result = organizer.start_organize(test_path)
        
        print("\n" + "="*50)
        print("Test Results Summary:")
        print("="*50)
        
        status = organizer.get_mock_status()
        for key, value in status.items():
            print(f"{key}: {value}")
        
        print(f"\nFolder mappings created: {len(result.get('folder_mappings', {}))}")
        print(f"Files to be moved: {len(result.get('file_paths', []))}")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] Mock test failed: {e}")
        return None


if __name__ == "__main__":
    # Run a quick test when script is executed directly
    test_result = test_mock_organizer()
    
    if test_result:
        print("\n[SUCCESS] Mock organizer test completed successfully!")
    else:
        print("\n[FAILED] Mock organizer test failed!")