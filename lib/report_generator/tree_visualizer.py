"""
樹狀結構視覺化工具
生成檔案分類的樹狀圖
"""
from typing import Dict, List
from datetime import datetime

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
    
    def generate_html_tree(self, folder_mappings: Dict[str, List[str]], title: str = "整理後結構") -> str:
        """
        生成HTML格式的樹狀結構圖，使用顏色區分層級
        
        Args:
            folder_mappings: 資料夾映射字典
            title: 樹狀圖標題
            
        Returns:
            HTML格式的樹狀結構
        """
        html_parts = []
        
        # HTML頭部和CSS樣式
        html_parts.append("""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>檔案整理樹狀結構圖</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', 'Arial', sans-serif;
            background-color: #f5f5f5;
            margin: 20px;
            line-height: 1.6;
        }
        
        .tree-container {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .tree-header {
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .tree-title {
            font-size: 24px;
            font-weight: bold;
            color: #1a237e;
            margin: 0;
        }
        
        .tree-timestamp {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }
        
        .tree {
            list-style: none;
            padding-left: 0;
        }
        
        .tree ul {
            list-style: none;
            padding-left: 25px;
            position: relative;
        }
        
        .tree li {
            position: relative;
            padding: 5px 0;
        }
        
        /* 樹狀線條 */
        .tree li::before {
            content: '';
            position: absolute;
            left: -20px;
            top: 15px;
            width: 15px;
            height: 1px;
            background-color: #ccc;
        }
        
        .tree li::after {
            content: '';
            position: absolute;
            left: -20px;
            top: 0;
            bottom: -5px;
            width: 1px;
            background-color: #ccc;
        }
        
        .tree li:last-child::after {
            height: 20px;
        }
        
        /* 根層級 - 深藍色 */
        .level-0 {
            color: #1a237e;
            font-size: 20px;
            font-weight: bold;
            padding: 10px;
            background-color: #e8eaf6;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        /* 第一層資料夾 - 中藍色 */
        .folder-level-1 {
            color: #3949ab;
            font-weight: bold;
            font-size: 16px;
            padding: 5px 10px;
            background-color: #e8eaf6;
            border-radius: 4px;
            display: inline-block;
            margin: 2px 0;
        }
        
        /* 第二層資料夾 - 淺藍色 */
        .folder-level-2 {
            color: #5c6bc0;
            font-weight: bold;
            font-size: 15px;
            padding: 4px 8px;
            background-color: #f3f4fb;
            border-radius: 3px;
            display: inline-block;
            margin: 2px 0;
        }
        
        /* 檔案 - 灰色 */
        .file {
            color: #757575;
            font-size: 14px;
            padding: 3px 8px;
            background-color: #fafafa;
            border-radius: 3px;
            display: inline-block;
            margin: 2px 0;
        }
        
        /* 檔案數量標記 */
        .file-count {
            color: #fff;
            background-color: #ff6b6b;
            padding: 2px 6px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 8px;
        }
        
        /* 圖示 */
        .icon {
            margin-right: 5px;
        }
        
        /* 省略標記 */
        .ellipsis {
            color: #999;
            font-style: italic;
            font-size: 13px;
        }
        
        /* 懸停效果 */
        .folder-level-1:hover,
        .folder-level-2:hover {
            transform: translateX(5px);
            transition: transform 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .file:hover {
            background-color: #f0f0f0;
            transition: background-color 0.2s ease;
        }
        
        /* 打印樣式 */
        @media print {
            body {
                background-color: white;
            }
            .tree-container {
                box-shadow: none;
                border: 1px solid #ddd;
            }
        }
    </style>
</head>
<body>
    <div class="tree-container">
        <div class="tree-header">
            <h1 class="tree-title">檔案整理樹狀結構圖</h1>
            <div class="tree-timestamp">生成時間: """ + f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + """</div>
        </div>
        <ul class="tree">
""")
        
        # 根目錄
        html_parts.append(f'            <li class="level-0"><span class="icon">📁</span>{title}</li>\n')
        html_parts.append('            <li>\n                <ul>\n')
        
        # 排序資料夾
        sorted_folders = sorted(folder_mappings.items())
        
        for folder_name, files in sorted_folders:
            # 資料夾項目
            file_count = len(files)
            html_parts.append(f'                    <li>\n')
            html_parts.append(f'                        <div class="folder-level-1">\n')
            html_parts.append(f'                            <span class="icon">📁</span>{folder_name}\n')
            html_parts.append(f'                            <span class="file-count">{file_count}個檔案</span>\n')
            html_parts.append(f'                        </div>\n')
            
            # 檔案列表
            if files:
                html_parts.append('                        <ul>\n')
                
                if len(files) <= 3:
                    # 顯示所有檔案
                    for file_name in files:
                        html_parts.append(f'                            <li><div class="file"><span class="icon">📄</span>{file_name}</div></li>\n')
                else:
                    # 顯示前2個和最後1個
                    html_parts.append(f'                            <li><div class="file"><span class="icon">📄</span>{files[0]}</div></li>\n')
                    html_parts.append(f'                            <li><div class="file"><span class="icon">📄</span>{files[1]}</div></li>\n')
                    if len(files) > 3:
                        html_parts.append(f'                            <li><div class="ellipsis">... ({len(files) - 3} 個其他檔案)</div></li>\n')
                    html_parts.append(f'                            <li><div class="file"><span class="icon">📄</span>{files[-1]}</div></li>\n')
                
                html_parts.append('                        </ul>\n')
            
            html_parts.append('                    </li>\n')
        
        # HTML結尾
        html_parts.append("""                </ul>
            </li>
        </ul>
    </div>
</body>
</html>""")
        
        return ''.join(html_parts)