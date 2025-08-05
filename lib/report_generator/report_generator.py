"""
報告生成器
整合樹狀圖、統計資料，生成完整的整理報告
"""
import os
import json
from datetime import datetime
from typing import Dict, Optional, List
from .tree_visualizer import TreeVisualizer
from .statistics_calculator import StatisticsCalculator

class ReportGenerator:
    def __init__(self, target_path: str):
        self.target_path = target_path
        self.tree_visualizer = TreeVisualizer()
        self.stats_calculator = StatisticsCalculator()
        self.report_dir = os.path.join(target_path, "tidy_report")
        
    def generate_reports(self, backup_path: Optional[str] = None) -> Dict[str, str]:
        """
        生成所有報告
        
        Args:
            backup_path: 備份資料夾路徑，如果未提供則使用預設路徑
            
        Returns:
            包含各報告檔案路徑的字典
        """
        # 確定備份路徑
        if not backup_path:
            backup_path = os.path.join(self.target_path, ".backup")
        
        # 載入資料
        file_paths_file = os.path.join(backup_path, "file_paths.json")
        summ_load_file = os.path.join(backup_path, "summ_load.json")
        
        if not os.path.exists(file_paths_file):
            raise FileNotFoundError(f"找不到備份檔案: {file_paths_file}")
        
        with open(file_paths_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        # 載入摘要資料（如果存在）
        summaries = {}
        if os.path.exists(summ_load_file):
            with open(summ_load_file, 'r', encoding='utf-8') as f:
                summ_data = json.load(f)
                for item in summ_data.get("summaries", []):
                    summaries[item["name"]] = item["summary"]
        
        # 生成時間戳記和日期資料夾
        now = datetime.now()
        date_folder = now.strftime("%Y%m%d_%H%M%S")
        report_subfolder = os.path.join(self.report_dir, date_folder)
        
        # 建立日期子資料夾
        os.makedirs(report_subfolder, exist_ok=True)
        
        # 生成各種報告
        report_files = {}
        
        # 1. 生成樹狀結構報告
        tree_file = os.path.join(report_subfolder, "tree_structure.html")
        self._generate_tree_report(file_data["folder_mappings"], tree_file)
        report_files["tree"] = tree_file
        
        # 2. 生成Markdown報告
        md_file = os.path.join(report_subfolder, "organize_report.md")
        self._generate_markdown_report(file_data, summaries, md_file)
        report_files["markdown"] = md_file
        
        # 3. 生成統計報告
        stats_file = os.path.join(report_subfolder, "statistics.txt")
        self._generate_statistics_report(file_data["folder_mappings"], file_data["file_paths"], stats_file)
        report_files["statistics"] = stats_file
        
        # 儲存報告資料夾路徑
        report_files["report_folder"] = report_subfolder
        
        return report_files
    
    def _generate_tree_report(self, folder_mappings: Dict, output_file: str):
        """生成樹狀結構報告"""
        # 生成HTML格式的樹狀結構
        html_content = self.tree_visualizer.generate_html_tree(folder_mappings)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_markdown_report(self, file_data: Dict, summaries: Dict, output_file: str):
        """生成Markdown格式報告"""
        folder_mappings = file_data["folder_mappings"]
        
        md_lines = [
            "# 檔案整理報告",
            "",
            f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**整理路徑**: `{self.target_path}`",
            "",
            "## 📊 整理概況",
            ""
        ]
        
        # 統計資料
        stats = self.stats_calculator.calculate_statistics(folder_mappings, file_data["file_paths"])
        md_lines.extend([
            f"- **總檔案數**: {stats['total_files']} 個",
            f"- **總資料夾數**: {stats['total_folders']} 個",
            f"- **分類時間**: {file_data.get('classification_time', 'N/A')}",
            "",
            "## 📁 資料夾結構",
            "",
            "```",
            self.tree_visualizer.generate_simple_tree(folder_mappings),
            "```",
            "",
            "## 📋 詳細分類",
            ""
        ])
        
        # 各資料夾詳情
        for folder_name in sorted(folder_mappings.keys()):
            files = folder_mappings[folder_name]
            md_lines.extend([
                f"### {folder_name}",
                f"*共 {len(files)} 個檔案*",
                ""
            ])
            
            # 檔案列表
            for file_name in sorted(files):
                # 如果有摘要，顯示摘要
                if file_name in summaries:
                    summary = summaries[file_name][:100] + "..." if len(summaries[file_name]) > 100 else summaries[file_name]
                    summary = summary.replace('\n', ' ')
                    md_lines.append(f"- **{file_name}**")
                    md_lines.append(f"  - {summary}")
                else:
                    md_lines.append(f"- {file_name}")
            
            md_lines.append("")
        
        # 統計圖表
        md_lines.extend([
            "## 📈 統計分析",
            "",
            "### 檔案分佈",
            "",
            "```"
        ])
        md_lines.append(self.stats_calculator.generate_text_chart(folder_mappings))
        md_lines.extend(["```", ""])
        
        # 統計摘要
        md_lines.extend([
            "### 統計摘要",
            "",
            self.stats_calculator.generate_summary(stats),
            "",
            "---",
            "*報告由檔案整理系統自動生成*"
        ])
        
        # 寫入檔案
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_lines))
    
    def _generate_statistics_report(self, folder_mappings: Dict, file_paths: List[Dict], output_file: str):
        """生成統計報告"""
        stats = self.stats_calculator.calculate_statistics(folder_mappings, file_paths)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("檔案整理統計報告\n")
            f.write("=" * 60 + "\n")
            f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            # 統計摘要
            f.write(self.stats_calculator.generate_summary(stats))
            f.write("\n\n")
            
            # 統計圖表
            f.write(self.stats_calculator.generate_text_chart(folder_mappings))
            f.write("\n\n")
            
            # 詳細資料夾統計
            f.write("詳細資料夾統計\n")
            f.write("-" * 40 + "\n")
            for folder_name, details in sorted(stats["folder_details"].items()):
                f.write(f"{folder_name:<30} {details['file_count']:>5} 個檔案 ({details['percentage']:>5.1f}%)\n")