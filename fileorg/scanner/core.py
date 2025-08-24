from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fileorg.scanner.helpers import get_file_info, save_scan_result, print_scan_summary

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
        # 忽略的資料夾名稱
        self.ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 
                           '.idea', '.vscode', 'tidy_report', '.backup', 'Organized_Files_*'}
        
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
                
                # 跳過忽略清單中的資料夾
                if item.is_dir() and item.name in self.ignore_dirs:
                    continue
                
                # 跳過符合特定模式的資料夾 (如 Organized_Files_*)
                if item.is_dir() and item.name.startswith('Organized_Files_'):
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

    def scan_with_details(self, save_result: bool = True, output_file: str = "scan_result.json") -> Dict[str, Any]:
        """
        執行詳細掃描並返回完整資訊
        
        Args:
            save_result: 是否保存掃描結果到檔案
            output_file: 輸出檔案名稱
            
        Returns:
            包含完整掃描結果的字典
        """
        print(f"開始掃描: {self.target_path}")
        
        # 獲取檔案路徑列表
        file_paths = self.scan_directory()
        
        # 收集檔案詳細資訊
        file_details = []
        for file_path_str in file_paths:
            file_path = Path(file_path_str)
            file_info = get_file_info(file_path)
            file_details.append(file_info)
        
        # 組織掃描結果
        scan_result = {
            "scan_time": datetime.now().isoformat(),
            "target_path": str(self.target_path.absolute()),
            "original_files": file_details
        }
        
        print(f"掃描完成: 找到 {len(file_details)} 個檔案")
        
        
        # 顯示掃描摘要
        print_scan_summary(scan_result)
        
        # 保存掃描結果（如果需要）
        if save_result:
            save_scan_result(scan_result, output_file)
        
        return scan_result
        