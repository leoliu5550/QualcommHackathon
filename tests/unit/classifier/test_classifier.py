"""
Classifier 模組單元測試
測試檔案分類與資料夾命名功能
"""

import pytest
from unittest.mock import Mock, patch
from fileorg.classifier.classifier import CreateFolderNamer


class TestCreateFolderNamer:
    """CreateFolderNamer 類別測試"""

    # ==================== 正常測試案例 ====================

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_create_folder_name_normal(self, mock_get_llm):
        """測試正常的資料夾名稱生成"""
        # 設定 mock
        mock_llm = Mock()
        mock_llm.inference.return_value = "MachineLearning"
        mock_get_llm.return_value = mock_llm

        # 建立實例並測試
        namer = CreateFolderNamer()
        content = "This is a document about deep learning and neural networks"
        result = namer.create_folder_name(content)

        assert result == "MachineLearning"
        mock_llm.inference.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_remapping_folder_single(self, mock_get_llm):
        """測試單一資料夾的重新映射"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()
        candidate_folders = ["Documents"]

        # 單一資料夾不需要合併
        result = namer.remapping_folder(candidate_folders)

        assert len(result) == 1
        assert result[0]["foldername"] == "Documents"
        assert result[0]["groupname"] == "Documents"

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_remapping_folder_multiple(self, mock_get_llm):
        """測試多個資料夾的重新映射"""
        mock_llm = Mock()
        mock_llm.inference.return_value = '[{"foldername":"Finance", "groupname":"BusinessDocs"}, {"foldername":"Reports", "groupname":"BusinessDocs"}]'
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()
        candidate_folders = ["Finance", "Reports"]

        result = namer.remapping_folder(candidate_folders)

        assert len(result) == 2
        assert result[0]["groupname"] == "BusinessDocs"
        assert result[1]["groupname"] == "BusinessDocs"

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_process_files_complete_flow(self, mock_get_llm, mock_summaries_data):
        """測試完整的檔案處理流程"""
        # 設定 mock
        mock_llm = Mock()
        mock_llm.inference.side_effect = [
            "MachineLearning",
            "Finance",
            "Meeting",
            '[{"foldername":"MachineLearning", "groupname":"Technical"}, {"foldername":"Finance", "groupname":"Business"}, {"foldername":"Meeting", "groupname":"Business"}]',
        ]
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()
        result = namer.process_files(mock_summaries_data, "/output")

        assert "file_paths" in result
        assert len(result["file_paths"]) == 3

        # 驗證路徑映射
        for file_info in result["file_paths"]:
            assert "original" in file_info
            assert "new" in file_info
            assert file_info["new"].startswith("/output")

    @pytest.mark.unit
    @pytest.mark.classifier
    def test_clean_output_normal(self):
        """測試輸出清理功能"""
        namer = CreateFolderNamer()

        # 測試各種輸入
        test_cases = [
            ("Normal Text", "Normal Text"),
            ("文字with數字123", "文字with數字123"),
            ("Special!@#$%Characters", "SpecialCharacters"),
            ("  Spaces  ", "Spaces"),
            ("混合ABC中文123", "混合ABC中文123"),
        ]

        for input_text, expected in test_cases:
            result = namer.clean_output(input_text)
            assert result == expected

    # ==================== 異常測試案例 ====================

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_llm_inference_failure(self, mock_get_llm):
        """測試 LLM 推論失敗的處理"""
        mock_llm = Mock()
        mock_llm.inference.side_effect = Exception("LLM 錯誤")
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()

        with pytest.raises(Exception) as exc_info:
            namer.create_folder_name("測試內容")

        assert "LLM 錯誤" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_invalid_json_response(self, mock_get_llm):
        """測試無效 JSON 回應的處理"""
        mock_llm = Mock()
        mock_llm.inference.return_value = "InvalidJSON{{"
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()
        candidate_folders = ["Folder1", "Folder2"]

        # 應該返回原始映射
        result = namer.remapping_folder(candidate_folders)

        assert len(result) == 2
        assert result[0]["foldername"] == "Folder1"
        assert result[0]["groupname"] == "Folder1"

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_empty_summaries_data(self, mock_get_llm):
        """測試空的摘要資料"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()
        empty_data = {"summaries": []}

        result = namer.process_files(empty_data, "/output")

        assert "file_paths" in result
        assert len(result["file_paths"]) == 0

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_missing_summary_field(self, mock_get_llm):
        """測試缺少摘要欄位的處理"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()
        invalid_data = {
            "summaries": [
                {
                    "path": "/test/file.txt",
                    "name": "file.txt",
                    # 缺少 summary 欄位
                }
            ]
        }

        with pytest.raises(KeyError):
            namer.process_files(invalid_data, "/output")

    # ==================== 邊緣測試案例 ====================

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_extremely_long_content(self, mock_get_llm):
        """測試極長內容的處理"""
        mock_llm = Mock()
        mock_llm.inference.return_value = "LongDocument"
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()
        long_content = "x" * 10000  # 超長內容

        # 應該只取前 500 個字元
        result = namer.create_folder_name(long_content)

        assert result == "LongDocument"
        # 驗證傳遞給 LLM 的內容被截斷
        call_args = mock_llm.inference.call_args
        assert len(str(call_args)) < 10000

    @pytest.mark.unit
    @pytest.mark.classifier
    def test_clean_output_edge_cases(self):
        """測試清理輸出的邊緣案例"""
        namer = CreateFolderNamer()

        edge_cases = [
            ("", ""),  # 空字串
            ("   ", ""),  # 只有空格
            ("！@#￥%……&*（）", ""),  # 只有特殊字元
            ("😀😃😄", ""),  # Emoji
            ("\n\t\r", ""),  # 控制字元
        ]

        for input_text, expected in edge_cases:
            result = namer.clean_output(input_text)
            assert result == expected

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_unicode_handling(self, mock_get_llm):
        """測試 Unicode 字元處理"""
        mock_llm = Mock()
        mock_llm.inference.return_value = "中文資料夾"
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()
        unicode_content = "這是包含中文、English、にほんご的內容"

        result = namer.create_folder_name(unicode_content)
        assert result == "中文資料夾"

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_special_path_characters(self, mock_get_llm):
        """測試路徑特殊字元的處理"""
        mock_llm = Mock()
        mock_llm.inference.return_value = "Folder/With/Slashes"
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()
        result = namer.create_folder_name("測試內容")

        # 斜線應該被移除
        cleaned = namer.clean_output(result)
        assert "/" not in cleaned

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_concurrent_processing_simulation(self, mock_get_llm):
        """模擬並發處理的情況"""
        mock_llm = Mock()
        mock_llm.inference.return_value = "ConcurrentFolder"
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()

        # 模擬多個檔案同時處理
        results = []
        for i in range(10):
            result = namer.create_folder_name(f"Content {i}")
            results.append(result)

        assert len(results) == 10
        assert all(r == "ConcurrentFolder" for r in results)

    @pytest.mark.unit
    @pytest.mark.classifier
    @patch("fileorg.classifier.classifier.get_llm")
    def test_partial_json_recovery(self, mock_get_llm):
        """測試部分 JSON 的恢復機制"""
        mock_llm = Mock()
        # 返回不完整的 JSON
        mock_llm.inference.return_value = '{"foldername":"Test", "groupname":"Group"'
        mock_get_llm.return_value = mock_llm

        namer = CreateFolderNamer()
        candidate_folders = ["Test"]

        # 應該嘗試修復並處理
        result = namer.remapping_folder(candidate_folders)

        # 因為 JSON 解析失敗，應返回原始映射
        assert len(result) == 1
        assert result[0]["foldername"] == "Test"
        assert result[0]["groupname"] == "Test"
