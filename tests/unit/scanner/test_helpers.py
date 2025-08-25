"""
Scanner Helpers 測試
"""

import pytest
from fileorg.scanner.helpers import get_file_info


class TestScannerHelpers:
    """Scanner helpers 測試"""

    @pytest.mark.unit
    def test_get_file_info(self, temp_dir):
        """測試獲取檔案資訊"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        file_info = get_file_info(str(test_file))

        assert file_info is not None
        assert file_info.get("path") == str(test_file)

    @pytest.mark.unit
    def test_get_file_info_nonexistent(self):
        """測試獲取不存在檔案的資訊"""
        file_info = get_file_info("/nonexistent/file.txt")

        # 應該優雅處理不存在的檔案，返回包含錯誤資訊的字典
        assert file_info is not None
        assert "error" in file_info
        assert file_info["is_readable"] is False
