"""
Organizer 模組單元測試
測試檔案整理的核心流程
"""
import pytest
import os
import json
import shutil
from unittest.mock import Mock, patch
from fileorg.core.organizer import Organizer


class TestOrganizer:
    """Organizer 類別測試"""
    
    # ==================== 正常測試案例 ====================
    
    @pytest.mark.unit
    @pytest.mark.organizer
    def test_organizer_initialization(self):
        """測試 Organizer 初始化"""
        organizer = Organizer()
        assert organizer is not None
    
    @pytest.mark.unit
    @pytest.mark.organizer
    @patch('fileorg.core.organizer.FileScanner')
    def test_file_scanner_integration(self, mock_scanner_class, temp_dir):
        """測試檔案掃描整合"""
        # 設定 mock
        mock_scanner = Mock()
        mock_scanner.scan_with_details.return_value = {
            "original_files": [
                {"path": str(temp_dir / "file1.txt")},
                {"path": str(temp_dir / "file2.pdf")}
            ]
        }
        mock_scanner_class.return_value = mock_scanner
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        result = organizer._file_scanner()
        
        assert len(result) == 2
        assert str(temp_dir / "file1.txt") in result
    
    @pytest.mark.unit
    @pytest.mark.organizer
    @patch('fileorg.core.organizer.parser_manager')
    def test_file_parser_integration(self, mock_parser_manager, temp_dir):
        """測試檔案解析整合"""
        # 設定 mock
        mock_result = Mock()
        mock_result.content = "測試內容"
        mock_parser_manager.parse_multiple_files.return_value = [mock_result]
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        scanner_result = [str(temp_dir / "test.txt")]
        result = organizer._file_parser(scanner_result, save_result=False)
        
        assert "summaries" in result
        assert len(result["summaries"]) == 1
        assert result["summaries"][0]["summary"] == "測試內容"
    
    @pytest.mark.unit
    @pytest.mark.organizer
    @patch('fileorg.core.organizer.create_name')
    def test_generate_folder_structure(self, mock_create_name, temp_dir):
        """測試資料夾結構生成"""
        # 設定 mock
        mock_create_name.process_files.return_value = {
            "file_paths": [
                {
                    "original": str(temp_dir / "file1.txt"),
                    "new": str(temp_dir / "Documents" / "file1.txt")
                }
            ]
        }
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        file_parsed = {"summaries": [{"summary": "test", "path": "file1.txt", "name": "file1.txt"}]}
        result = organizer._generate_folder(file_parsed, str(temp_dir), save_result=False)
        
        assert "folder_mappings" in result
        assert "file_paths" in result
        assert "classification_time" in result
    
    @pytest.mark.unit
    @pytest.mark.organizer
    def test_move_files_success(self, temp_dir):
        """測試成功移動檔案"""
        # 建立測試檔案
        source_file = temp_dir / "source.txt"
        source_file.write_text("內容")
        
        target_dir = temp_dir / "target"
        
        organizer = Organizer()
        generate_result = {
            "file_paths": [
                {
                    "original": str(source_file),
                    "new": str(target_dir / "source.txt")
                }
            ]
        }
        
        organizer._move_file(generate_result)
        
        assert not source_file.exists()
        assert (target_dir / "source.txt").exists()
    
    @pytest.mark.unit
    @pytest.mark.organizer
    @patch('fileorg.core.organizer.ReportGenerator')
    def test_generate_reports(self, mock_report_class, temp_dir):
        """測試報告生成"""
        # 設定 mock
        mock_report = Mock()
        mock_report.generate_reports.return_value = {
            "report_folder": str(temp_dir / "reports"),
            "tree": "tree.html",
            "markdown": "report.md",
            "statistics": "stats.txt"
        }
        mock_report_class.return_value = mock_report
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        organizer._generate_reports()
        
        mock_report.generate_reports.assert_called_once()
    
    # ==================== 異常測試案例 ====================
    
    @pytest.mark.unit
    @pytest.mark.organizer
    def test_move_file_source_not_exists(self, temp_dir, capsys):
        """測試移動不存在的檔案"""
        organizer = Organizer()
        generate_result = {
            "file_paths": [
                {
                    "original": str(temp_dir / "nonexistent.txt"),
                    "new": str(temp_dir / "target" / "file.txt")
                }
            ]
        }
        
        organizer._move_file(generate_result)
        
        captured = capsys.readouterr()
        assert "Failed to move" in captured.out
    
    @pytest.mark.unit
    @pytest.mark.organizer
    def test_move_file_permission_error(self, temp_dir, monkeypatch):
        """測試權限錯誤的處理"""
        source_file = temp_dir / "source.txt"
        source_file.write_text("內容")
        
        # 模擬權限錯誤
        def mock_move(*args, **kwargs):
            raise PermissionError("沒有權限")
        
        monkeypatch.setattr(shutil, "move", mock_move)
        
        organizer = Organizer()
        generate_result = {
            "file_paths": [
                {
                    "original": str(source_file),
                    "new": str(temp_dir / "target" / "file.txt")
                }
            ]
        }
        
        organizer._move_file(generate_result)
        
        # 檔案應該仍在原位
        assert source_file.exists()
    
    @pytest.mark.unit
    @pytest.mark.organizer
    @patch('fileorg.core.organizer.ReportGenerator')
    def test_report_generation_failure(self, mock_report_class, temp_dir, capsys):
        """測試報告生成失敗的處理"""
        # 設定 mock 拋出異常
        mock_report = Mock()
        mock_report.generate_reports.side_effect = Exception("報告生成錯誤")
        mock_report_class.return_value = mock_report
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        organizer._generate_reports()
        
        captured = capsys.readouterr()
        assert "生成報告時發生錯誤" in captured.out
    
    @pytest.mark.unit
    @pytest.mark.organizer
    def test_save_result_with_encoding_issues(self, temp_dir):
        """測試儲存結果時的編碼問題"""
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        # 包含特殊字元的資料
        file_parsed = {
            "summaries": [
                {
                    "summary": "內容包含特殊字元：\u2603 ☃ 😀",
                    "path": "特殊.txt",
                    "name": "特殊.txt"
                }
            ]
        }
        
        result = organizer._file_parser([], save_result=True)
        
        # 驗證備份檔案存在且可讀取
        backup_file = temp_dir / ".backup" / "summ_load.json"
        if backup_file.exists():
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # JSON 應該正確處理特殊字元
    
    # ==================== 邊緣測試案例 ====================
    
    @pytest.mark.unit
    @pytest.mark.organizer
    def test_empty_directory_processing(self, temp_dir):
        """測試處理空目錄"""
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        scanner_result = []
        result = organizer._file_parser(scanner_result, save_result=False)
        
        assert result["summaries"] == []
    
    @pytest.mark.unit
    @pytest.mark.organizer
    def test_large_file_batch_processing(self, temp_dir):
        """測試大批量檔案處理"""
        # 建立多個測試檔案
        files = []
        for i in range(50):
            file_path = temp_dir / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
            files.append(str(file_path))
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        # 測試解析大量檔案
        with patch('fileorg.core.organizer.parser_manager') as mock_parser:
            mock_result = Mock()
            mock_result.content = "parsed"
            mock_parser.parse_multiple_files.return_value = [mock_result] * 50
            
            result = organizer._file_parser(files, save_result=False)
            
            assert len(result["summaries"]) == 50
    
    @pytest.mark.unit
    @pytest.mark.organizer
    def test_duplicate_filename_handling(self, temp_dir):
        """測試重複檔名的處理"""
        # 建立同名但不同路徑的檔案
        (temp_dir / "dir1").mkdir()
        (temp_dir / "dir2").mkdir()
        
        file1 = temp_dir / "dir1" / "same.txt"
        file2 = temp_dir / "dir2" / "same.txt"
        file1.write_text("內容1")
        file2.write_text("內容2")
        
        organizer = Organizer()
        generate_result = {
            "file_paths": [
                {
                    "original": str(file1),
                    "new": str(temp_dir / "target" / "same.txt")
                },
                {
                    "original": str(file2),
                    "new": str(temp_dir / "target" / "same.txt")
                }
            ]
        }
        
        # 第二個檔案應該覆蓋第一個
        organizer._move_file(generate_result)
        
        assert not file1.exists()
        assert not file2.exists()
        assert (temp_dir / "target" / "same.txt").exists()
    
    @pytest.mark.unit
    @pytest.mark.organizer
    def test_circular_path_prevention(self, temp_dir):
        """測試防止循環路徑"""
        source = temp_dir / "file.txt"
        source.write_text("內容")
        
        organizer = Organizer()
        
        # 嘗試將檔案移動到自己
        generate_result = {
            "file_paths": [
                {
                    "original": str(source),
                    "new": str(source)  # 相同路徑
                }
            ]
        }
        
        organizer._move_file(generate_result)
        
        # 檔案應該保持不變
        assert source.exists()
        assert source.read_text() == "內容"
    
    @pytest.mark.unit
    @pytest.mark.organizer
    @pytest.mark.parametrize("file_count", [0, 1, 10, 100])
    def test_various_file_counts(self, temp_dir, file_count):
        """測試不同數量的檔案處理"""
        files = []
        for i in range(file_count):
            file_path = temp_dir / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
            files.append({
                "original": str(file_path),
                "new": str(temp_dir / "organized" / f"file_{i}.txt")
            })
        
        organizer = Organizer()
        generate_result = {"file_paths": files}
        
        organizer._move_file(generate_result)
        
        # 驗證所有檔案都被移動
        if file_count > 0:
            assert (temp_dir / "organized").exists()
            assert len(list((temp_dir / "organized").iterdir())) == file_count
    
    @pytest.mark.unit
    @pytest.mark.organizer
    def test_path_normalization(self, temp_dir):
        """測試路徑正規化"""
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        # 測試相對路徑轉換
        file_parsed = {"summaries": []}
        
        with patch('fileorg.core.organizer.create_name') as mock_create:
            mock_create.process_files.return_value = {
                "file_paths": [
                    {
                        "original": "./file.txt",
                        "new": "./organized/file.txt"
                    }
                ]
            }
            
            result = organizer._generate_folder(file_parsed, str(temp_dir))
            
            # 路徑應該被轉換為絕對路徑
            for file_info in result["file_paths"]:
                assert os.path.isabs(file_info["new"])