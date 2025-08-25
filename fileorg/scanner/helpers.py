import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Union


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    獲取檔案詳細資訊

    Args:
        file_path: 檔案路徑物件或字串

    Returns:
        包含檔案資訊的字典
    """
    # 如果是字串，轉換為 Path 物件
    if isinstance(file_path, str):
        file_path = Path(file_path)

    try:
        stat_info = file_path.stat()

        # 檢查檔案是否可讀
        is_readable = os.access(file_path, os.R_OK)

        # 修改時間格式化
        modified_time = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        # 建立時間格式化
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
        # 如果無法獲取資訊，返回基本資訊
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
    """
    將掃描結果保存為 JSON 檔案

    Args:
        scan_data: 掃描結果資料
        output_file: 輸出檔案名稱
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(scan_data, f, ensure_ascii=False, indent=2)
        print(f"掃描結果已保存至: {output_file}")
    except Exception as e:
        print(f"保存檔案時發生錯誤: {e}")


def print_scan_summary(scan_data: Dict[str, Any]):
    """
    列印掃描結果摘要

    Args:
        scan_data: 掃描結果資料
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
