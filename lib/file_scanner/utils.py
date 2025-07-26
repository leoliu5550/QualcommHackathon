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


    

if __name__ == "__main__":
    # 測試 format_file_size 函數
    test_sizes = [0, 1023, 1024, 2048, 1048576, 1073741824]
    for size in test_sizes:
        print(f"{size} bytes = {format_file_size(size)}")