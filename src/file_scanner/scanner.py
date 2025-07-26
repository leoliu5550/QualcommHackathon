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
    
    def scan_directory(self) -> List[str]:
        """
        掃描目錄並返回檔案路徑清單
        
        Returns:
            檔案路徑字串列表
        """
        self.scanned_files = []
        
        try:
            # 遍歷目錄中的所有項目
            for item in self.target_path.iterdir():
                if item.is_file():
                    # 跳過隱藏檔案
                    if not item.name.startswith('.'):
                        self.scanned_files.append(str(item))
                        
        except PermissionError:
            print(f"警告: 無權限存取 {self.target_path}")
        except Exception as e:
            print(f"掃描錯誤: {e}")
            
        return self.scanned_files


if __name__ == "__main__":
    # 簡單測試
    try:
        scanner = FileScanner(".")
        print(f"掃描器初始化成功，目標路徑: {scanner.target_path}")
        
        files = scanner.scan_directory()
        print(f"找到 {len(files)} 個檔案:")
        
        # 顯示前 5 個檔案
        for i, file_path in enumerate(files[:5]):
            print(f"  {i+1}. {Path(file_path).name}")
            
    except Exception as e:
        print(f"錯誤: {e}")
