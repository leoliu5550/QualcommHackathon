import json
from pathlib import Path

from fileorg.report_generator.ports import ClassificationReport, ClassificationReportHtmlPort, FilePathEntry
from fileorg.report_generator.web_template.web_template import build_web_html_template


class HtmlReportGenerator(ClassificationReportHtmlPort):
    """
    Adapter implementation for generating HTML classification reports.
    """

    def generate_html(self, report: ClassificationReport, root_dir: Path) -> Path:
        """
        Generate an HTML file that visualizes file classification results.

        This method creates an HTML report from a ClassificationReport instance.
        The HTML file is saved as 'ClassificationReport.html' inside the
        '.backup' subdirectory of the specified root directory. All necessary
        parent directories are created automatically.

        Args:
            report: The classification report data containing timestamp and
                file path entries to be visualized.
            root_dir: The target directory where the HTML file will be written.
                The actual file will be created at root_dir/.backup/ClassificationReport.html.

        Returns:
            The full path to the generated HTML file.

        Raises:
            OSError: If the output directory cannot be created or the file
                cannot be written.
            TypeError: If report is not a ClassificationReport instance.
        """

        # Default output file name
        output_path = Path(root_dir) / ".backup" / "ClassificationReport.html"

        # 自動建立所有不存在的資料夾
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Dataclass → dict → JSON string
        raw_dict = {
            "timestamp": report.timestamp,
            "file_paths": [
                {
                    "initial_path": fp.initial_path,
                    "original": fp.original,
                    "new": fp.new,
                }
                for fp in report.file_paths
            ],
        }

        json_str = json.dumps(raw_dict, ensure_ascii=False, indent=8)

        # HTML 模板
        html_template = build_web_html_template(json_str=json_str)
        # 寫入 HTML 檔案
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)

        print(f"HTML 檔案已成功生成於: {output_path}")
        return output_path

    def load_report_from_json(self, json_path: Path) -> ClassificationReport:
        """
        Load a classification report from a JSON file and convert it into dataclasses.

        Args:
            json_path (Path): Path to the JSON file containing the classification report.

        Returns:
            ClassificationReport: A dataclass instance representing the report.
        """
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        return ClassificationReport(
            timestamp=raw["timestamp"],
            file_paths=[FilePathEntry(**fp) for fp in raw["file_paths"]],
        )

    def load_report_from_dict(self, data: dict) -> ClassificationReport:
        """
        Convert a dictionary into a ClassificationReport dataclass instance.

        Args:
            data (dict): Dictionary containing 'timestamp' and 'file_paths' keys.
                        'file_paths' should be a list of dictionaries with keys
                        'initial_path', 'original', and 'new'.

        Returns:
            ClassificationReport: A dataclass instance representing the report.
        """
        return ClassificationReport(
            timestamp=data["timestamp"],
            file_paths=[FilePathEntry(**fp) for fp in data["file_paths"]],
        )


# 使用範例
if __name__ == "__main__":
    # 使用字典
    sample_data = {
        "timestamp": "2025-11-16T01:38:54.952020",
        "file_paths": [
            {
                "initial_path": "Air_Quality_Data/aqx_p_432.csv",
                "original": "Air_Quality_Data/aqx_p_432.csv",
                "new": "Air_Quality_Reports/aqx_p_432.csv",
            },
            {
                "initial_path": "Air_Pollution/air-quality-guide-for-particle-pollution.pdf",
                "original": "Air_Pollution/air-quality-guide-for-particle-pollution.pdf",
                "new": "Air_Pollution/air-quality-guide-for-particle-pollution.pdf",
            },
            {
                "initial_path": "Requirements/Customer_Requirements1/customer_order.md",
                "original": "Requirements/Customer_Requirements/customer_order.md",
                "new": "Requirements/Customer_Requirements/customer_order.md",
            },
            {
                "initial_path": "Requirements/Customer_Requirements123/customer_order222.md",
                "original": "Requirements/Customer_Requirements/customer_order222.md",
                "new": "Requirements/Customer_Requirements/customer_order222.md",
            },
        ],
    }

    html_generator = HtmlReportGenerator()
    report = html_generator.load_report_from_dict(sample_data)
    output_path = html_generator.generate_html(report, Path("./output"))

    from pathlib import Path

    sample_data_path = Path("/Users/leoliu/Desktop/example2/.backup/file_paths.json")
    html_generator = HtmlReportGenerator()
    report = html_generator.load_report_from_json(sample_data_path)
    output_path = html_generator.generate_html(report, Path("./output2"))

    report = ClassificationReport(
        timestamp="2025-11-16T03:05:54.249034",
        file_paths=[
            FilePathEntry(
                initial_path="src/file1.txt",
                original="src/file1.txt",
                new="Text_Files/file1.txt",
            ),
            FilePathEntry(
                initial_path="docs/readme.md",
                original="docs/readme.md",
                new="Documentation/readme.md",
            ),
            FilePathEntry(
                initial_path="docs/readme2.md",
                original="docs/readme2.md",
                new="Documentation/readme2.md",
            ),
        ],
    )
    html_generator = HtmlReportGenerator()
    output_path = html_generator.generate_html(report, Path("./output3"))
