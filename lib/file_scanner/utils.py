import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """
    獲取檔案詳細資訊
    
    Args:
        file_path: 檔案路徑物件
        
    Returns:
        包含檔案資訊的字典
    """
    try:
        stat_info = file_path.stat()
        
        # 檢查檔案是否可讀
        is_readable = os.access(file_path, os.R_OK)
        
        # 修改時間格式化
        modified_time = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        
        return {
            "path": str(file_path.absolute()),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size": stat_info.st_size,
            "modified_time": modified_time,
            "is_readable": is_readable
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
            "error": str(e)
        }
    
def format_file_size(size_bytes: int) -> str:
    """
    格式化檔案大小顯示
    
    Args:
        size_bytes: 檔案大小（位元組）
        
    Returns:
        格式化後的大小字串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size = size_bytes
    i = 0
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def save_scan_result(scan_data: Dict[str, Any], output_file: str = "scan_result.json"):
    """
    將掃描結果保存為 JSON 檔案
    
    Args:
        scan_data: 掃描結果資料
        output_file: 輸出檔案名稱
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
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
    files = scan_data.get('original_files', [])
    total_files = len(files)
    total_size = sum(f.get('size', 0) for f in files)
    
    print(f"\n📊 掃描摘要:")
    print(f"掃描時間: {scan_data.get('scan_time', 'N/A')}")
    print(f"目標路徑: {scan_data.get('target_path', 'N/A')}")
    print(f"檔案總數: {total_files}")
    print(f"總大小: {format_file_size(total_size)}")
    
    # 統計副檔名
    extensions = {}
    for file_info in files:
        ext = file_info.get('extension', '無副檔名')
        if not ext:
            ext = '無副檔名'
        extensions[ext] = extensions.get(ext, 0) + 1
    
    if extensions:
        print(f"\n📋 檔案類型統計:")
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {ext}: {count} 個檔案")
    

if __name__ == "__main__":
    # 測試save_scan_result和print_scan_summary函數
    test_data = {
        "scan_time": "2023-10-01T12:00:00",
        "target_path": "/path/to/scan",
        "original_files": [
            {
                "path": "/path/to/scan/file1.txt",
                "name": "file1.txt",
                "extension": ".txt",
                "size": 1234,
                "modified_time": "2023-10-01T11:59:59",
                "is_readable": True                                             
            },
            {
                "path": "/path/to/scan/file2.pdf",
                "name": "file2.pdf",
                "extension": ".pdf",
                "size": 5678,
                "modified_time": "2023-10-01T11:59:58",
                "is_readable": True
            }
        ]
    }
    save_scan_result(test_data, "test_scan_result.json")
    print_scan_summary(test_data)