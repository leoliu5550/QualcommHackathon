"""
樹狀結構視覺化工具
生成檔案分類的樹狀圖
"""
from typing import Dict, List

class TreeVisualizer:
    def __init__(self):
        # 樹狀圖符號
        self.BRANCH = "├── "
        self.LAST_BRANCH = "└── "
        self.VERTICAL = "│   "
        self.EMPTY = "    "
        
    def generate_tree(self, folder_mappings: Dict[str, List[str]], title: str = "整理後結構") -> str:
        """
        生成樹狀結構圖
        
        Args:
            folder_mappings: 資料夾映射字典
            title: 樹狀圖標題
            
        Returns:
            樹狀結構字串
        """
        tree_lines = [f"📁 {title}"]
        
        # 排序資料夾
        sorted_folders = sorted(folder_mappings.items())
        total_folders = len(sorted_folders)
        
        for idx, (folder_name, files) in enumerate(sorted_folders):
            is_last_folder = idx == total_folders - 1
            
            # 資料夾行
            folder_prefix = self.LAST_BRANCH if is_last_folder else self.BRANCH
            file_count = len(files)
            tree_lines.append(f"{folder_prefix}📁 {folder_name} ({file_count}個檔案)")
            
            # 檔案行（只顯示前2個和最後1個作為範例）
            if files:
                file_prefix = self.EMPTY if is_last_folder else self.VERTICAL
                
                if len(files) <= 3:
                    # 顯示所有檔案
                    for file_idx, file_name in enumerate(files):
                        is_last_file = file_idx == len(files) - 1
                        file_branch = self.LAST_BRANCH if is_last_file else self.BRANCH
                        tree_lines.append(f"{file_prefix}{file_branch}📄 {file_name}")
                else:
                    # 顯示前2個和最後1個
                    tree_lines.append(f"{file_prefix}{self.BRANCH}📄 {files[0]}")
                    tree_lines.append(f"{file_prefix}{self.BRANCH}📄 {files[1]}")
                    if len(files) > 3:
                        tree_lines.append(f"{file_prefix}{self.BRANCH}... ({len(files) - 3} 個其他檔案)")
                    tree_lines.append(f"{file_prefix}{self.LAST_BRANCH}📄 {files[-1]}")
        
        return "\n".join(tree_lines)
    
    def generate_simple_tree(self, folder_mappings: Dict[str, List[str]]) -> str:
        """
        生成簡單樹狀結構（不含檔案細節）
        """
        tree_lines = ["📁 整理後結構"]
        
        sorted_folders = sorted(folder_mappings.items())
        total_folders = len(sorted_folders)
        
        for idx, (folder_name, files) in enumerate(sorted_folders):
            is_last = idx == total_folders - 1
            prefix = self.LAST_BRANCH if is_last else self.BRANCH
            tree_lines.append(f"{prefix}📁 {folder_name} ({len(files)}個檔案)")
        
        return "\n".join(tree_lines)