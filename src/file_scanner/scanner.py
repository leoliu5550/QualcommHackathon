from pathlib import Path
from typing import List, Dict, Any, Optional

class FileScanner:
    """檔案掃描器類別"""
    
    def __init__(self, target_path: str, max_depth: Optional[int] = None):
        """
        初始化檔案掃描器
        
        Args:
            target_path: 要掃描的目標路徑
            max_depth: 最大掃描深度，None 表示無限制
        """
        self.target_path = Path(target_path)
        self.max_depth = max_depth
        self.scanned_files = []
        
        # 基本路徑驗證
        if not self.target_path.exists():
            raise FileNotFoundError(f"目標路徑不存在: {target_path}")
        
        if not self.target_path.is_dir():
            raise NotADirectoryError(f"目標路徑不是資料夾: {target_path}")

    def scan_directory(self) -> List[str]:
        """
        掃描目錄並返回檔案路徑清單（支援遞迴）
        
        Returns:
            檔案路徑字串列表
        """
        self.scanned_files = []
        self._recursive_scan(self.target_path, 0)
        return self.scanned_files
    
    def _recursive_scan(self, current_path: Path, current_depth: int):
        """
        遞迴掃描資料夾
        
        Args:
            current_path: 目前掃描的路徑
            current_depth: 目前的深度
        """
        # 檢查深度限制
        if self.max_depth is not None and current_depth > self.max_depth:
            return
            
        try:
            for item in current_path.iterdir():
                # 跳過隱藏檔案和資料夾
                if item.name.startswith('.'):
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


if __name__ == "__main__":
    # 測試遞迴掃描功能
    try:
        # 測試基本掃描
        scanner = FileScanner(".", max_depth=2)
        print(f"掃描器初始化成功，目標路徑: {scanner.target_path}")
        
        files = scanner.scan_directory()
        print(f"找到 {len(files)} 個檔案 (最大深度: 2)")
        
        # 按資料夾分組顯示
        folders = {}
        for file_path in files[:10]:  # 只顯示前 10 個
            path_obj = Path(file_path)
            folder = str(path_obj.parent)
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(path_obj.name)
        
        for folder, files_in_folder in folders.items():
            print(f"\n📁 {folder}:")
            for file_name in files_in_folder[:3]:  # 每個資料夾最多顯示 3 個檔案
                print(f"  - {file_name}")
            if len(files_in_folder) > 3:
                print(f"  ... 還有 {len(files_in_folder) - 3} 個檔案")
            
    except Exception as e:
        print(f"錯誤: {e}")