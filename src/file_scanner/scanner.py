from pathlib import Path
from typing import List, Dict, Any, Optional


class FileScanner:
    """檔案掃描器類別"""
    
    def __init__(self, target_path: str):
        """
        初始化檔案掃描器
        
        Args:
            target_path: 要掃描的目標路徑
        """
        self.target_path = Path(target_path)
        self.scanned_files = []
        
        # 基本路徑驗證
        if not self.target_path.exists():
            raise FileNotFoundError(f"目標路徑不存在: {target_path}")
        
        if not self.target_path.is_dir():
            raise NotADirectoryError(f"目標路徑不是資料夾: {target_path}")


if __name__ == "__main__":
    # 簡單測試
    try:
        scanner = FileScanner(".")
        print(f"掃描器初始化成功，目標路徑: {scanner.target_path}")
    except Exception as e:
        print(f"初始化失敗: {e}")
