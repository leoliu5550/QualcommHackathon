"""
真實檔案整合測試
使用 textIO 資料夾中的實際檔案測試完整流程
"""
import pytest
import json
import shutil
from pathlib import Path
from unittest.mock import patch, Mock


class TestRealFileOrganization:
    """測試真實檔案的完整整理流程"""
    
    @pytest.mark.integration
    def test_textio_files_parsing(self, textio_samples):
        """測試 textIO 資料夾中所有檔案的解析"""
        from fileorg.parsers import parser_manager
        
        # 收集所有檔案
        test_files = []
        for file_path in textio_samples.iterdir():
            if file_path.is_file():
                test_files.append(str(file_path))
        
        # 解析所有檔案
        results = parser_manager.parse_multiple_files(test_files)
        
        # 驗證解析結果
        successful_parses = 0
        failed_files = []
        
        for result, file_path in zip(results, test_files):
            if result.success:
                successful_parses += 1
                # 驗證內容不為空
                assert result.content != "", f"檔案 {file_path} 解析成功但內容為空"
                # 驗證檔案類型正確 (file_type 可能沒有點號)
                expected_type = Path(file_path).suffix.lower()
                assert result.file_type == expected_type or result.file_type == expected_type.lstrip('.')
            else:
                failed_files.append((file_path, result.error))
        
        # 報告結果
        print(f"\n成功解析: {successful_parses}/{len(test_files)} 個檔案")
        if failed_files:
            print("失敗的檔案:")
            for file_path, error in failed_files:
                print(f"  - {Path(file_path).name}: {error}")
        
        # 至少 80% 的檔案應該成功解析
        assert successful_parses >= len(test_files) * 0.8
    
    @pytest.mark.integration
    def test_textio_scanning(self, textio_samples):
        """測試掃描 textIO 資料夾"""
        from fileorg.scanner import FileScanner
        
        scanner = FileScanner(str(textio_samples))
        
        # 執行掃描
        result = scanner.scan_with_details(save_result=False)
        
        # 驗證掃描結果
        assert "original_files" in result
        assert len(result["original_files"]) > 0
        
        # 檢查特定檔案是否被找到
        file_names = [f["name"] for f in result["original_files"]]
        expected_files = [
            "CH04account.pdf",
            "Excel_Function.xlsx",
            "HealthOrganizations.docx",
            "Short Stories.pdf",
            "Small Changes in AI.pptx",
            "customer_order.json",
            "customer_order.md"
        ]
        
        for expected in expected_files:
            assert expected in file_names, f"未找到預期的檔案: {expected}"
    
    @pytest.mark.integration
    @patch('fileorg.classifier.classifier.get_llm')
    def test_complete_workflow_with_textio(self, mock_get_llm, textio_samples, tmp_path):
        """測試使用 textIO 檔案的完整工作流程"""
        # 複製測試檔案到臨時目錄
        test_dir = tmp_path / "test_organize"
        shutil.copytree(textio_samples, test_dir)
        
        # 設定 mock LLM
        mock_llm = Mock()
        mock_llm.inference.side_effect = self._smart_llm_responses
        mock_get_llm.return_value = mock_llm
        
        from fileorg.core.organizer import Organizer
        
        organizer = Organizer()
        organizer.target_path = str(test_dir)
        
        # 步驟 1: 掃描
        scan_result = organizer._file_scanner()
        assert len(scan_result) >= 7, "應該找到至少 7 個檔案"
        
        # 步驟 2: 解析
        parse_result = organizer._file_parser(scan_result, save_result=True)
        assert len(parse_result["summaries"]) == len(scan_result)
        
        # 驗證每個檔案都有摘要
        for summary in parse_result["summaries"]:
            assert summary["summary"] != ""
            assert summary["name"] != ""
        
        # 步驟 3: 分類
        folder_result = organizer._generate_folder(
            parse_result, 
            str(test_dir), 
            save_result=True
        )
        
        # 驗證分類結果
        assert "file_paths" in folder_result
        assert "folder_mappings" in folder_result
        
        # 檢查是否合理分類
        folders = list(folder_result["folder_mappings"].keys())
        assert len(folders) > 0, "應該至少生成一個分類資料夾"
        assert len(folders) <= 5, "不應該為每個檔案都建立獨立資料夾"
        
        # 步驟 4: 移動檔案
        organizer._move_file(folder_result)
        
        # 驗證檔案已移動
        for file_info in folder_result["file_paths"]:
            new_path = Path(file_info["new"])
            assert new_path.exists(), f"檔案未移動到: {new_path}"
            
            old_path = Path(file_info["original"])
            assert not old_path.exists(), f"原始檔案仍存在: {old_path}"
    
    @pytest.mark.integration
    def test_specific_file_types(self, filetype_samples):
        """測試特定檔案類型的處理"""
        from fileorg.parsers import parser_manager
        
        test_cases = {
            ".docx": "111學生自主學習計畫.docx",
            ".pdf": "Short Stories.pdf",
            ".csv": "aqx_p_432.csv",
            ".json": "customer_order.json",
            ".md": "customer_order.md",
            ".html": "raw_text.html",
            ".pptx": "raw_text.pptx",
            ".xlsx": "raw_text.xlsx",
            ".txt": "書僕.txt"
        }
        
        for ext, filename in test_cases.items():
            file_path = filetype_samples / filename
            if file_path.exists():
                result = parser_manager.parse_file(str(file_path))
                
                # 基本驗證
                assert result.success, f"{filename} 解析失敗: {result.error}"
                # file_type 可能沒有點號
                assert result.file_type == ext or result.file_type == ext.lstrip('.')
                assert len(result.content) > 0, f"{filename} 內容為空"
                
                # 特定類型驗證
                if ext == ".json":
                    # JSON 應該包含結構化內容
                    assert "{" in result.content or "[" in result.content
                elif ext == ".csv":
                    # CSV 應該包含逗號分隔的內容
                    assert "," in result.content or "\n" in result.content
                elif ext == ".html":
                    # HTML 內容應該被提取（不含標籤）
                    assert "<html>" not in result.content.lower()
    
    @pytest.mark.integration
    def test_chinese_filename_handling(self, filetype_samples):
        """測試中文檔名處理"""
        from fileorg.scanner import FileScanner
        from fileorg.parsers import parser_manager
        
        # 找出中文檔名的檔案
        chinese_files = [
            "111學生自主學習計畫.docx",
            "書僕.txt"
        ]
        
        for filename in chinese_files:
            file_path = filetype_samples / filename
            if file_path.exists():
                # 測試解析
                result = parser_manager.parse_file(str(file_path))
                assert result.success, f"中文檔名 {filename} 解析失敗"
                
                # 測試掃描器能正確處理
                scanner = FileScanner(str(filetype_samples))
                scan_result = scanner.scan_directory()
                
                # 確認中文檔名在掃描結果中
                scanned_names = [Path(p).name for p in scan_result]
                assert filename in scanned_names
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_performance_with_real_files(self, textio_samples, benchmark_timer):
        """測試真實檔案的處理效能"""
        from fileorg.parsers import parser_manager
        
        # 收集所有檔案
        test_files = [str(f) for f in textio_samples.iterdir() if f.is_file()]
        
        # 測試解析效能
        benchmark_timer.start()
        results = parser_manager.parse_multiple_files(test_files)
        parse_time = benchmark_timer.stop()
        
        print(f"\n解析 {len(test_files)} 個檔案耗時: {parse_time:.2f} 秒")
        print(f"平均每個檔案: {parse_time/len(test_files):.3f} 秒")
        
        # 效能標準：平均每個檔案不超過 1 秒
        assert parse_time / len(test_files) < 1.0
    
    @pytest.mark.integration
    def test_backup_creation(self, textio_samples, tmp_path):
        """測試備份檔案的建立"""
        # 複製測試檔案
        test_dir = tmp_path / "backup_test"
        shutil.copytree(textio_samples, test_dir)
        
        from fileorg.core.organizer import Organizer
        
        with patch('fileorg.classifier.classifier.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.inference.return_value = "TestFolder"
            mock_get_llm.return_value = mock_llm
            
            organizer = Organizer()
            organizer.target_path = str(test_dir)
            
            # 執行部分流程
            scan_result = organizer._file_scanner()
            parse_result = organizer._file_parser(scan_result, save_result=True)
            
            # 檢查備份檔案
            backup_dir = test_dir / ".backup"
            assert backup_dir.exists(), "備份目錄未建立"
            
            summ_file = backup_dir / "summ_load.json"
            assert summ_file.exists(), "摘要備份檔案未建立"
            
            # 驗證備份內容
            with open(summ_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            assert "summaries" in backup_data
            assert len(backup_data["summaries"]) == len(scan_result)
    
    # ==================== 輔助方法 ====================
    
    def _smart_llm_responses(self, *args, **kwargs):
        """智慧 LLM 回應模擬，根據檔案內容分類"""
        prompt_str = str(args[0]) if args else str(kwargs.get('prompt', ''))
        
        # 根據內容關鍵字分類
        if "folder name" in prompt_str.lower():
            if "excel" in prompt_str.lower() or "function" in prompt_str.lower():
                return "Spreadsheets"
            elif "health" in prompt_str.lower() or "organization" in prompt_str.lower():
                return "Documents"
            elif "story" in prompt_str.lower() or "stories" in prompt_str.lower():
                return "Literature"
            elif "ai" in prompt_str.lower() or "changes" in prompt_str.lower():
                return "Presentations"
            elif "account" in prompt_str.lower() or "ch04" in prompt_str.lower():
                return "Academic"
            elif "customer" in prompt_str.lower() or "order" in prompt_str.lower():
                return "BusinessData"
            elif "cluster" in prompt_str.lower() or "analysis" in prompt_str.lower():
                return "Academic"
            else:
                return "General"
        elif "categorize" in prompt_str.lower():
            # 合併相似的類別
            return '''[
                {"foldername": "Spreadsheets", "groupname": "DataFiles"},
                {"foldername": "Documents", "groupname": "Documents"},
                {"foldername": "Literature", "groupname": "Documents"},
                {"foldername": "Presentations", "groupname": "Presentations"},
                {"foldername": "Academic", "groupname": "Academic"},
                {"foldername": "BusinessData", "groupname": "DataFiles"}
            ]'''
        
        return "DefaultFolder"