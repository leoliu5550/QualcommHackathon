"""Scanner helper utilities.

Provides file information extraction and result formatting.
Supports scan result saving and summary generation.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Union


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get detailed file information.

    Extracts metadata like size, timestamps, and permissions.
    Handles errors gracefully with fallback values.

    Args:
        file_path: File path as string or Path object

    Returns:
        Dict with file metadata (path, name, size, times, etc.)
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    try:
        stat_info = file_path.stat()

        # Check read permission
        is_readable = os.access(file_path, os.R_OK)

        # Format timestamps
        modified_time = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        created_time = datetime.fromtimestamp(stat_info.st_ctime).isoformat()

        return {
            "path": str(file_path.absolute()),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size": stat_info.st_size,
            "modified_time": modified_time,
            "created_time": created_time,
            "is_readable": is_readable,
        }
    except Exception as e:
        # Return basic info on error
        return {
            "path": str(file_path.absolute()),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size": 0,
            "modified_time": None,
            "is_readable": False,
            "error": str(e),
        }


def save_scan_result(scan_data: Dict[str, Any], output_file: str = "scan_result.json"):
    """Save scan results to JSON file.

    Args:
        scan_data: Scan result dictionary
        output_file: Output filename
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(scan_data, f, ensure_ascii=False, indent=2)
        print(f"Scan results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving file: {e}")


def print_scan_summary(scan_data: Dict[str, Any]):
    """Print scan results summary.

    Shows file count, size distribution, and type breakdown.

    Args:
        scan_data: Scan result dictionary
    """
    files = scan_data.get("original_files", [])
    total_files = len(files)
    total_size = sum(f.get("size", 0) for f in files)

    print("\n📊 掃描摘要:")
    print(f"掃描時間: {scan_data.get('scan_time', 'N/A')}")
    print(f"目標路徑: {scan_data.get('target_path', 'N/A')}")
    print(f"檔案總數: {total_files}")
    print(f"總大小: {total_size} bytes")

    # 統計副檔名
    extensions = {}
    for file_info in files:
        ext = file_info.get("extension", "無副檔名")
        if not ext:
            ext = "無副檔名"
        extensions[ext] = extensions.get(ext, 0) + 1

    if extensions:
        print("\n📋 檔案類型統計:")
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {ext}: {count} 個檔案")
