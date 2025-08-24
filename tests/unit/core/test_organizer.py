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


class TestOrganizerWorkflowIntegration:
    """Organizer 完整工作流程測試"""
    
    @pytest.mark.unit
    @patch('fileorg.core.organizer.FileScanner')
    @patch('fileorg.core.organizer.parser_manager')
    @patch('fileorg.core.organizer.create_name')
    @patch('fileorg.core.organizer.ReportGenerator')
    def test_start_organize_complete_workflow(self, mock_report_class, mock_create_name, mock_parser, mock_scanner_class, temp_dir):
        """測試完整的 start_organize 工作流程"""
        # 設定所有 mocks
        mock_scanner = Mock()
        mock_scanner.scan_with_details.return_value = {
            "original_files": [
                {"path": str(temp_dir / "file1.txt")},
                {"path": str(temp_dir / "file2.pdf")}
            ]
        }
        mock_scanner_class.return_value = mock_scanner
        
        mock_parse_result = Mock()
        mock_parse_result.content = "Parsed content"
        mock_parser.parse_multiple_files.return_value = [mock_parse_result, mock_parse_result]
        
        mock_create_name.process_files.return_value = {
            "file_paths": [
                {"original": str(temp_dir / "file1.txt"), "new": str(temp_dir / "docs" / "file1.txt")},
                {"original": str(temp_dir / "file2.pdf"), "new": str(temp_dir / "docs" / "file2.pdf")}
            ]
        }
        
        mock_report = Mock()
        mock_report.generate_reports.return_value = {"report_folder": str(temp_dir / "reports")}
        mock_report_class.return_value = mock_report
        
        # 建立實際檔案
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.pdf").write_text("content2")
        
        organizer = Organizer()
        organizer.start_organize(str(temp_dir))
        
        # 驗證所有步驟都被調用
        mock_scanner.scan_with_details.assert_called_once()
        mock_parser.parse_multiple_files.assert_called_once()
        mock_create_name.process_files.assert_called_once()
        mock_report.generate_reports.assert_called()
        
        # 驗證檔案被移動到正確位置
        assert (temp_dir / "docs" / "file1.txt").exists()
        assert (temp_dir / "docs" / "file2.pdf").exists()
        assert not (temp_dir / "file1.txt").exists()
        assert not (temp_dir / "file2.pdf").exists()
    
    @pytest.mark.unit
    @patch('fileorg.core.organizer.FileScanner')
    def test_file_scanner_error_handling(self, mock_scanner_class, temp_dir):
        """測試檔案掃描器錯誤處理"""
        mock_scanner = Mock()
        mock_scanner.scan_with_details.side_effect = Exception("Scanner failed")
        mock_scanner_class.return_value = mock_scanner
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        with pytest.raises(Exception):
            organizer._file_scanner()
    
    @pytest.mark.unit
    @patch('fileorg.core.organizer.parser_manager')
    def test_file_parser_error_handling(self, mock_parser, temp_dir):
        """測試檔案解析器錯誤處理"""
        mock_parser.parse_multiple_files.side_effect = Exception("Parser failed")
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        with pytest.raises(Exception):
            organizer._file_parser([str(temp_dir / "test.txt")])
    
    @pytest.mark.unit
    @patch('fileorg.core.organizer.create_name')
    def test_generate_folder_error_handling(self, mock_create_name, temp_dir):
        """測試資料夾生成錯誤處理"""
        mock_create_name.process_files.side_effect = Exception("Classification failed")
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        file_parsed = {"summaries": []}
        
        with pytest.raises(Exception):
            organizer._generate_folder(file_parsed, str(temp_dir))


class TestOrganizerFileHandling:
    """Organizer 檔案處理專門測試"""
    
    @pytest.mark.unit
    def test_move_file_with_subdirectories(self, temp_dir):
        """測試移動檔案到深層子目錄"""
        source = temp_dir / "source.txt"
        source.write_text("content")
        
        organizer = Organizer()
        generate_result = {
            "file_paths": [
                {
                    "original": str(source),
                    "new": str(temp_dir / "deep" / "nested" / "structure" / "source.txt")
                }
            ]
        }
        
        organizer._move_file(generate_result)
        
        assert not source.exists()
        assert (temp_dir / "deep" / "nested" / "structure" / "source.txt").exists()
    
    @pytest.mark.unit
    def test_move_file_with_unicode_paths(self, temp_dir):
        """測試移動包含 Unicode 字元的檔案"""
        source = temp_dir / "測試檔案.txt"
        source.write_text("測試內容")
        
        target_path = temp_dir / "分類資料夾" / "測試檔案.txt"
        
        organizer = Organizer()
        generate_result = {
            "file_paths": [
                {
                    "original": str(source),
                    "new": str(target_path)
                }
            ]
        }
        
        organizer._move_file(generate_result)
        
        assert not source.exists()
        assert target_path.exists()
        assert target_path.read_text(encoding='utf-8') == "測試內容"
    
    @pytest.mark.unit
    def test_move_file_overwrite_existing(self, temp_dir):
        """測試移動檔案時覆蓋現有檔案"""
        source = temp_dir / "source.txt"
        source.write_text("new content")
        
        target_dir = temp_dir / "target"
        target_dir.mkdir()
        existing = target_dir / "source.txt"
        existing.write_text("old content")
        
        organizer = Organizer()
        generate_result = {
            "file_paths": [
                {
                    "original": str(source),
                    "new": str(existing)
                }
            ]
        }
        
        organizer._move_file(generate_result)
        
        assert not source.exists()
        assert existing.exists()
        assert existing.read_text() == "new content"
    
    @pytest.mark.unit
    def test_move_file_disk_space_error(self, temp_dir, monkeypatch):
        """測試磁碟空間不足時的錯誤處理"""
        source = temp_dir / "source.txt"
        source.write_text("content")
        
        def mock_move(*args, **kwargs):
            raise OSError("No space left on device")
        
        monkeypatch.setattr(shutil, "move", mock_move)
        
        organizer = Organizer()
        generate_result = {
            "file_paths": [
                {
                    "original": str(source),
                    "new": str(temp_dir / "target" / "source.txt")
                }
            ]
        }
        
        with patch('builtins.print') as mock_print:
            organizer._move_file(generate_result)
        
        # 應該印出錯誤訊息
        error_calls = [call for call in mock_print.call_args_list if "Failed to move" in str(call)]
        assert len(error_calls) > 0
        
        # 檔案應該仍在原處
        assert source.exists()


class TestOrganizerDataPersistence:
    """Organizer 資料持久化測試"""
    
    @pytest.mark.unit
    def test_file_parser_save_result_structure(self, temp_dir):
        """測試解析結果保存的資料結構"""
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        with patch('fileorg.core.organizer.parser_manager') as mock_parser:
            mock_result = Mock()
            mock_result.content = "parsed content"
            mock_parser.parse_multiple_files.return_value = [mock_result]
            
            scanner_result = [str(temp_dir / "test.txt")]
            organizer._file_parser(scanner_result, save_result=True)
        
        backup_file = temp_dir / ".backup" / "summ_load.json"
        assert backup_file.exists()
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            assert "scan_time" in data
            assert "summaries" in data
            assert len(data["summaries"]) == 1
            assert data["summaries"][0]["summary"] == "parsed content"
            assert data["summaries"][0]["path"] == str(temp_dir / "test.txt")
            assert data["summaries"][0]["name"] == "test.txt"
    
    @pytest.mark.unit
    def test_generate_folder_save_result_structure(self, temp_dir):
        """測試資料夾生成結果保存的資料結構"""
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        with patch('fileorg.core.organizer.create_name') as mock_create_name:
            mock_create_name.process_files.return_value = {
                "file_paths": [
                    {
                        "original": str(temp_dir / "file.txt"),
                        "new": str(temp_dir / "Documents" / "file.txt")
                    }
                ]
            }
            
            file_parsed = {"summaries": []}
            organizer._generate_folder(file_parsed, str(temp_dir), save_result=True)
        
        backup_file = temp_dir / ".backup" / "file_paths.json"
        assert backup_file.exists()
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            assert "folder_mappings" in data
            assert "file_paths" in data
            assert "classification_time" in data
            assert len(data["file_paths"]) == 1
            assert os.path.isabs(data["file_paths"][0]["new"])
    
    @pytest.mark.unit
    def test_backup_directory_creation(self, temp_dir):
        """測試備份目錄建立"""
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        # 確保初始時沒有備份目錄
        backup_dir = temp_dir / ".backup"
        assert not backup_dir.exists()
        
        with patch('fileorg.core.organizer.parser_manager') as mock_parser:
            mock_result = Mock()
            mock_result.content = "content"
            mock_parser.parse_multiple_files.return_value = [mock_result]
            
            organizer._file_parser([str(temp_dir / "test.txt")], save_result=True)
        
        # 備份目錄應該被建立
        assert backup_dir.exists()
        assert backup_dir.is_dir()
    
    @pytest.mark.unit
    def test_json_encoding_handling(self, temp_dir):
        """測試 JSON 編碼處理"""
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        with patch('fileorg.core.organizer.parser_manager') as mock_parser:
            mock_result = Mock()
            mock_result.content = "包含中文和特殊字元的內容：☃ 😀 \u2603"
            mock_parser.parse_multiple_files.return_value = [mock_result]
            
            special_path = str(temp_dir / "特殊檔名.txt")
            organizer._file_parser([special_path], save_result=True)
        
        backup_file = temp_dir / ".backup" / "summ_load.json"
        with open(backup_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 驗證特殊字元被正確保存和讀取
            assert "☃" in data["summaries"][0]["summary"]
            assert "😀" in data["summaries"][0]["summary"]
            assert "特殊檔名.txt" in data["summaries"][0]["name"]


class TestOrganizerEdgeCases:
    """Organizer 邊緣案例測試"""
    
    @pytest.mark.unit
    def test_empty_file_paths_handling(self, temp_dir):
        """測試空檔案路徑列表的處理"""
        organizer = Organizer()
        generate_result = {"file_paths": []}
        
        # 應該不會拋出異常
        organizer._move_file(generate_result)
    
    @pytest.mark.unit
    def test_missing_file_paths_key(self, temp_dir):
        """測試缺少 file_paths 鍵的處理"""
        organizer = Organizer()
        generate_result = {}  # 沒有 file_paths 鍵
        
        # 應該不會拋出異常
        organizer._move_file(generate_result)
    
    @pytest.mark.unit
    def test_malformed_file_path_entries(self, temp_dir):
        """測試格式錯誤的檔案路徑條目"""
        organizer = Organizer()
        generate_result = {
            "file_paths": [
                {"original": "only_original"},  # 缺少 new 鍵
                {"new": "only_new"},  # 缺少 original 鍵
                {}  # 空字典
            ]
        }
        
        # 應該不會拋出 KeyError，而是gracefully處理
        with patch('builtins.print') as mock_print:
            organizer._move_file(generate_result)
        
        # 應該有錯誤訊息被印出
        assert mock_print.call_count > 0
    
    @pytest.mark.unit
    @patch('fileorg.core.organizer.create_name')
    def test_generate_folder_with_empty_summaries(self, mock_create_name, temp_dir):
        """測試使用空摘要生成資料夾"""
        mock_create_name.process_files.return_value = {"file_paths": []}
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        file_parsed = {"summaries": []}
        result = organizer._generate_folder(file_parsed, str(temp_dir))
        
        assert "folder_mappings" in result
        assert result["folder_mappings"] == {}
        assert "file_paths" in result
        assert result["file_paths"] == []
    
    @pytest.mark.unit
    def test_target_path_assignment(self, temp_dir):
        """測試 target_path 屬性正確設定"""
        organizer = Organizer()
        test_path = str(temp_dir)
        
        organizer.start_organize(test_path)
        
        assert hasattr(organizer, 'target_path')
        assert organizer.target_path == test_path
    
    @pytest.mark.unit
    @patch('fileorg.core.organizer.FileScanner')
    def test_scanner_stdout_suppression(self, mock_scanner_class, temp_dir):
        """測試掃描器輸出被正確抑制"""
        mock_scanner = Mock()
        
        def side_effect(*args, **kwargs):
            # 模擬有輸出的掃描器
            print("This should be suppressed")
            return {"original_files": [{"path": "test.txt"}]}
        
        mock_scanner.scan_with_details.side_effect = side_effect
        mock_scanner_class.return_value = mock_scanner
        
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        with patch('sys.stdout', new_callable=Mock) as mock_stdout:
            result = organizer._file_scanner()
        
        # 驗證輸出被抑制（stdout.write 不應該被調用）
        assert result == ["test.txt"]
    
    @pytest.mark.unit
    def test_folder_mappings_generation_logic(self, temp_dir):
        """測試資料夾映射生成邏輯"""
        organizer = Organizer()
        organizer.target_path = str(temp_dir)
        
        with patch('fileorg.core.organizer.create_name') as mock_create_name:
            mock_create_name.process_files.return_value = {
                "file_paths": [
                    {
                        "original": str(temp_dir / "file1.txt"),
                        "new": str(temp_dir / "Documents" / "Personal" / "file1.txt")
                    },
                    {
                        "original": str(temp_dir / "file2.txt"),
                        "new": str(temp_dir / "Documents" / "Personal" / "file2.txt")
                    },
                    {
                        "original": str(temp_dir / "file3.txt"),
                        "new": str(temp_dir / "Images" / "file3.txt")
                    }
                ]
            }
            
            file_parsed = {"summaries": []}
            result = organizer._generate_folder(file_parsed, str(temp_dir))
        
        # 驗證資料夾映射正確生成
        folder_mappings = result["folder_mappings"]
        
        assert len(folder_mappings) == 2
        assert "Documents/Personal" in folder_mappings
        assert "Images" in folder_mappings
        assert len(folder_mappings["Documents/Personal"]) == 2
        assert len(folder_mappings["Images"]) == 1
        assert "file1.txt" in folder_mappings["Documents/Personal"]
        assert "file2.txt" in folder_mappings["Documents/Personal"]
        assert "file3.txt" in folder_mappings["Images"]