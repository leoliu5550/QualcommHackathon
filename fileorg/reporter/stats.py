"""
統計計算工具
計算檔案分類的各項統計數據
"""

from typing import Dict, List
import os


class StatisticsCalculator:
    def __init__(self):
        pass

    def calculate_statistics(
        self, folder_mappings: Dict[str, List[str]], file_paths: List[Dict]
    ) -> Dict:
        """
        計算檔案整理統計資料

        Args:
            folder_mappings: 資料夾映射
            file_paths: 檔案路徑資訊

        Returns:
            統計資料字典
        """
        stats = {
            "total_files": sum(len(files) for files in folder_mappings.values()),
            "total_folders": len(folder_mappings),
            "folder_details": {},
            "file_extensions": {},
            "largest_folder": None,
            "smallest_folder": None,
        }

        # 計算每個資料夾的詳細資訊
        for folder_name, files in folder_mappings.items():
            stats["folder_details"][folder_name] = {
                "file_count": len(files),
                "percentage": (
                    round(len(files) / stats["total_files"] * 100, 1)
                    if stats["total_files"] > 0
                    else 0
                ),
            }

            # 統計副檔名
            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower() or "無副檔名"
                stats["file_extensions"][ext] = stats["file_extensions"].get(ext, 0) + 1

        # 找出最大和最小的資料夾
        if folder_mappings:
            sorted_folders = sorted(folder_mappings.items(), key=lambda x: len(x[1]))
            stats["smallest_folder"] = (sorted_folders[0][0], len(sorted_folders[0][1]))
            stats["largest_folder"] = (sorted_folders[-1][0], len(sorted_folders[-1][1]))

        return stats

    def generate_text_chart(
        self, folder_mappings: Dict[str, List[str]], max_width: int = 50
    ) -> str:
        """
        生成文字統計圖表

        Args:
            folder_mappings: 資料夾映射
            max_width: 圖表最大寬度

        Returns:
            文字圖表字串
        """
        if not folder_mappings:
            return "無資料"

        total_files = sum(len(files) for files in folder_mappings.values())
        if total_files == 0:
            return "無檔案"

        chart_lines = ["", "📊 檔案分類統計圖表", "=" * 60]

        # 排序並生成圖表
        sorted_folders = sorted(folder_mappings.items(), key=lambda x: len(x[1]), reverse=True)

        for folder_name, files in sorted_folders:
            file_count = len(files)
            percentage = file_count / total_files * 100
            bar_length = int(percentage / 100 * max_width)

            # 生成進度條
            bar = "█" * bar_length + "░" * (max_width - bar_length)

            # 格式化資料夾名稱（限制長度）
            display_name = folder_name[:20] + "..." if len(folder_name) > 23 else folder_name

            chart_lines.append(f"{display_name:<25} {bar} {file_count:>3} ({percentage:>5.1f}%)")

        chart_lines.append("=" * 60)

        return "\n".join(chart_lines)

    def generate_summary(self, stats: Dict) -> str:
        """
        生成統計摘要
        """
        summary_lines = [
            "📈 整理統計摘要",
            "-" * 40,
            f"總檔案數: {stats['total_files']} 個",
            f"總資料夾數: {stats['total_folders']} 個",
            (
                f"平均每個資料夾: {stats['total_files'] / stats['total_folders']:.1f} 個檔案"
                if stats["total_folders"] > 0
                else "平均每個資料夾: 0 個檔案"
            ),
            "",
            "📁 資料夾大小分布:",
        ]

        if stats["largest_folder"]:
            summary_lines.append(
                f"  最大: {stats['largest_folder'][0]} ({stats['largest_folder'][1]} 個檔案)"
            )
        if stats["smallest_folder"]:
            summary_lines.append(
                f"  最小: {stats['smallest_folder'][0]} ({stats['smallest_folder'][1]} 個檔案)"
            )

        # 副檔名統計
        if stats["file_extensions"]:
            summary_lines.extend(
                [
                    "",
                    "📄 檔案類型分布:",
                ]
            )
            sorted_exts = sorted(stats["file_extensions"].items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_exts[:5]:  # 只顯示前5個
                summary_lines.append(f"  {ext}: {count} 個")
            if len(sorted_exts) > 5:
                summary_lines.append(f"  其他: {sum(count for ext, count in sorted_exts[5:])} 個")

        return "\n".join(summary_lines)
