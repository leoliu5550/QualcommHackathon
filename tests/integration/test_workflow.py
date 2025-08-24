"""
整合測試 - 測試完整的檔案整理工作流程
"""
import pytest
import json
from unittest.mock import patch, Mock


class TestCompleteWorkflow:
    """完整工作流程整合測試"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_end_to_end_file_organization(self, temp_dir):
        """端到端的檔案整理測試"""
        # 建立測試檔案結構
        self._create_test_structure(temp_dir)
        
        # Mock LLM 以避免實際 API 呼叫
        with patch('fileorg.classifier.classifier.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.inference.side_effect = self._mock_llm_responses
            mock_get_llm.return_value = mock_llm
            
            from fileorg.core.organizer import Organizer
            
            organizer = Organizer()
            organizer.target_path = str(temp_dir)
            
            # 執行掃描
            scan_result = organizer._file_scanner()
            assert len(scan_result) >= 3
            
            # 執行解析
            parse_result = organizer._file_parser(scan_result, save_result=True)
            assert len(parse_result["summaries"]) >= 3
            
            # 執行分類
            folder_result = organizer._generate_folder(
                parse_result, 
                str(temp_dir), 
                save_result=True
            )
            assert "file_paths" in folder_result
            
            # 執行移動
            organizer._move_file(folder_result)
            
            # 驗證檔案已被移動到正確位置
            self._verify_organization(temp_dir)
    
    @pytest.mark.integration
    def test_preview_mode_workflow(self, temp_dir):
        """測試預覽模式工作流程"""
        self._create_test_structure(temp_dir)
        
        with patch('fileorg.classifier.classifier.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.inference.side_effect = self._mock_llm_responses
            mock_get_llm.return_value = mock_llm
            
            from fileorg.cli import run_preview_mode
            
            result = run_preview_mode(str(temp_dir))
            
            # 驗證預覽結果
            assert "file_paths" in result
            assert "folder_mappings" in result
            
            # 驗證檔案沒有被移動
            assert (temp_dir / "document.txt").exists()
            assert (temp_dir / "data.json").exists()
    
    @pytest.mark.integration
    def test_restore_workflow(self, temp_dir):
        """測試還原工作流程"""
        # 建立已整理的結構
        organized_dir = temp_dir / "Documents"
        organized_dir.mkdir()
        
        file1 = organized_dir / "file1.txt"
        file1.write_text("內容1")
        
        # 建立備份檔案
        backup_dir = temp_dir / ".backup"
        backup_dir.mkdir()
        
        backup_data = {
            "file_paths": [
                {
                    "original": str(temp_dir / "file1.txt"),
                    "new": str(file1)
                }
            ]
        }
        
        backup_file = backup_dir / "file_paths.json"
        backup_file.write_text(json.dumps(backup_data, ensure_ascii=False))
        
        # 執行還原
        from fileorg.restore.restore_folder import restore_folder
        restore_folder(str(temp_dir))
        
        # 驗證檔案已還原
        assert (temp_dir / "file1.txt").exists()
        assert not file1.exists()
    
    @pytest.mark.integration
    def test_cli_integration(self, temp_dir, monkeypatch):
        """測試 CLI 整合"""
        self._create_test_structure(temp_dir)
        
        # 模擬命令行參數
        import sys
        monkeypatch.setattr(sys, 'argv', ['fileorg', str(temp_dir), '--preview'])
        
        with patch('fileorg.classifier.classifier.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.inference.side_effect = self._mock_llm_responses
            mock_get_llm.return_value = mock_llm
            
            from fileorg.cli import main
            
            # 應該不會拋出異常
            try:
                main()
            except SystemExit as e:
                assert e.code == 0 or e.code is None
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_scale_organization(self, temp_dir):
        """測試大規模檔案整理"""
        # 建立大量檔案
        for i in range(50):
            file_path = temp_dir / f"file_{i}.txt"
            file_path.write_text(f"Content for file {i}")
        
        with patch('fileorg.classifier.classifier.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.inference.return_value = "TestFolder"
            mock_get_llm.return_value = mock_llm
            
            from fileorg.core.organizer import Organizer
            
            organizer = Organizer()
            organizer.target_path = str(temp_dir)
            
            # 執行完整流程
            scan_result = organizer._file_scanner()
            parse_result = organizer._file_parser(scan_result)
            folder_result = organizer._generate_folder(parse_result, str(temp_dir))
            organizer._move_file(folder_result)
            
            # 驗證所有檔案都被整理
            organized_files = list((temp_dir / "TestFolder").iterdir())
            assert len(organized_files) == 50
    
    @pytest.mark.integration
    def test_error_recovery(self, temp_dir):
        """測試錯誤恢復機制"""
        # 建立部分損壞的環境
        file1 = temp_dir / "good.txt"
        file1.write_text("正常內容")
        
        # 建立無法讀取的檔案（模擬）
        with patch('fileorg.parsers.manager.FileParserManager.parse_file') as mock_parse:
            # 第一個檔案解析失敗，第二個成功
            mock_parse.side_effect = [
                Mock(success=False, error="解析錯誤"),
                Mock(success=True, content="內容")
            ]
            
            from fileorg.core.organizer import Organizer
            
            organizer = Organizer()
            organizer.target_path = str(temp_dir)
            
            # 應該能繼續處理其他檔案
            result = organizer._file_parser([str(file1), str(file1)])
            assert len(result["summaries"]) == 2
    
    # ==================== 輔助方法 ====================
    
    def _create_test_structure(self, temp_dir):
        """建立測試用的檔案結構"""
        # 建立各種類型的檔案
        (temp_dir / "document.txt").write_text("This is a document about project management")
        (temp_dir / "data.json").write_text('{"type": "financial", "value": 1000}')
        (temp_dir / "report.md").write_text("# Monthly Report\n\nSales data analysis")
        
        # 建立子目錄和檔案
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("Nested file content")
    
    def _mock_llm_responses(self, *args, **kwargs):
        """模擬 LLM 回應"""
        # 簡單的回應邏輯
        prompt_str = str(args[0]) if args else str(kwargs.get('prompt', ''))
        
        if "folder name" in prompt_str.lower():
            if "project" in prompt_str:
                return "ProjectDocs"
            elif "financial" in prompt_str:
                return "Finance"
            else:
                return "General"
        elif "categorize" in prompt_str.lower():
            return '[{"foldername": "ProjectDocs", "groupname": "Work"}]'
        
        return "DefaultResponse"
    
    def _verify_organization(self, temp_dir):
        """驗證檔案組織結果"""
        # 檢查是否建立了新的資料夾
        subdirs = [d for d in temp_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        assert len(subdirs) > 0
        
        # 檢查檔案是否被移動
        original_files = [f for f in temp_dir.iterdir() if f.is_file()]
        # 應該只剩下很少的檔案在根目錄
        assert len(original_files) < 3