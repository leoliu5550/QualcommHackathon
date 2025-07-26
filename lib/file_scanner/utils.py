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

if __name__ == "__main__":
    # 測試 get_file_info 函數
    test_path = Path("test/data/filetype/書僕.txt")
    if test_path.exists():
        info = get_file_info(test_path)
        print(json.dumps(info, indent=4, ensure_ascii=False))
    else:
        print(f"檔案 {test_path} 不存在。")