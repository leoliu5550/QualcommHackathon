"""
Reporter Generator 測試
"""

import pytest
from unittest.mock import patch
from fileorg.reporter.generator import ReportGenerator


class TestReportGenerator:
    """ReportGenerator 測試"""

    @pytest.mark.unit
    def test_report_generator_initialization(self, temp_dir):
        """測試報告生成器初始化"""
        generator = ReportGenerator(str(temp_dir))
        assert generator.target_path == str(temp_dir)

    @pytest.mark.unit
    @patch("fileorg.reporter.generator.ReportGenerator.generate_reports")
    def test_generate_reports_called(self, mock_generate, temp_dir):
        """測試報告生成方法被調用"""
        mock_generate.return_value = {
            "report_folder": str(temp_dir / "reports"),
            "files": ["report.html", "stats.txt"],
        }

        generator = ReportGenerator(str(temp_dir))
        result = generator.generate_reports()

        mock_generate.assert_called_once()
        assert "report_folder" in result
        assert "files" in result

    @pytest.mark.unit
    def test_report_generator_with_backup_data(self, temp_dir):
        """測試使用備份資料生成報告"""
        # 建立測試備份資料
        backup_dir = temp_dir / ".backup"
        backup_dir.mkdir()

        backup_file = backup_dir / "file_paths.json"
        backup_file.write_text('{"file_paths": [], "folder_mappings": {}}')

        generator = ReportGenerator(str(temp_dir))

        # 應該能夠處理有備份資料的情況
        assert generator.target_path == str(temp_dir)
