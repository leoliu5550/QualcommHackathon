"""
Scanner 模組單元測試
涵蓋正常、異常、邊緣案例
"""
import pytest
from pathlib import Path
from fileorg.scanner.core import FileScanner
from fileorg.scanner.helpers import get_file_info, save_scan_result


class TestFileScanner:
    """FileScanner 類別的測試"""
    
    # ==================== 正常測試案例 ====================
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_scan_empty_directory(self, temp_dir):
        """測試掃描空目錄"""
        scanner = FileScanner(str(temp_dir))
        result = scanner.scan_directory()
        assert result == []
        assert isinstance(result, list)
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_scan_with_single_file(self, temp_dir):
        """測試掃描含單一檔案的目錄"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("測試內容")
        
        scanner = FileScanner(str(temp_dir))
        result = scanner.scan_directory()
        
        assert len(result) == 1
        assert str(test_file) in result
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_scan_with_multiple_files(self, sample_files):
        """測試掃描含多個檔案的目錄"""
        scanner = FileScanner(str(sample_files['text'].parent))
        result = scanner.scan_directory()
        
        # 應該找到所有建立的檔案
        assert len(result) >= 4  # text, json, empty, large, special
        
        # 驗證檔案路徑格式
        for file_path in result:
            assert Path(file_path).exists()
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_scan_nested_directories(self, nested_directory_structure):
        """測試掃描巢狀目錄結構"""
        scanner = FileScanner(str(nested_directory_structure))
        result = scanner.scan_directory()
        
        # 應該找到所有非忽略目錄中的檔案
        file_names = [Path(f).name for f in result]
        assert "root_file.txt" in file_names
        assert "level1_file.txt" in file_names
        assert "level2_file.txt" in file_names
        assert "level3_file.txt" in file_names
        
        # 不應該包含被忽略目錄中的檔案
        assert "ignored.txt" not in file_names
        assert "cache.pyc" not in file_names
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_scan_with_depth_limit(self, nested_directory_structure):
        """測試深度限制功能"""
        # 限制深度為 1
        scanner = FileScanner(str(nested_directory_structure), max_depth=1)
        result = scanner.scan_directory()
        
        file_names = [Path(f).name for f in result]
        assert "root_file.txt" in file_names
        assert "level1_file.txt" in file_names
        assert "level2_file.txt" not in file_names  # 超過深度限制
        assert "level3_file.txt" not in file_names
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_scan_with_details(self, scanner_test_dir):
        """測試詳細掃描功能"""
        scanner = FileScanner(str(scanner_test_dir))
        result = scanner.scan_with_details(save_result=False)
        
        assert "scan_time" in result
        assert "target_path" in result
        assert "original_files" in result
        assert isinstance(result["original_files"], list)
        
        # 驗證檔案詳細資訊
        if result["original_files"]:
            file_info = result["original_files"][0]
            assert "path" in file_info
            assert "name" in file_info
            assert "size" in file_info
            assert "extension" in file_info
    
    # ==================== 異常測試案例 ====================
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_invalid_path(self):
        """測試無效路徑"""
        with pytest.raises(FileNotFoundError) as exc_info:
            FileScanner("/不存在的路徑/test")
        assert "目標路徑不存在" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_file_as_directory(self, temp_dir):
        """測試將檔案當作目錄"""
        test_file = temp_dir / "file.txt"
        test_file.write_text("內容")
        
        with pytest.raises(NotADirectoryError) as exc_info:
            FileScanner(str(test_file))
        assert "目標路徑不是資料夾" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_permission_denied_handling(self, temp_dir, monkeypatch):
        """測試權限不足的處理"""
        # 模擬權限錯誤
        def mock_iterdir(self):
            raise PermissionError("模擬權限錯誤")
        
        monkeypatch.setattr(Path, "iterdir", mock_iterdir)
        
        scanner = FileScanner(str(temp_dir))
        result = scanner.scan_directory()
        
        # 應該優雅地處理錯誤，返回空列表
        assert result == []
    
    # ==================== 邊緣測試案例 ====================
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_scan_with_special_characters(self, temp_dir):
        """測試特殊字元檔名"""
        special_files = [
            "測試檔案.txt",
            "file with spaces.txt",
            "檔案！@#$%^&().txt",
            "emoji😀.txt"
        ]
        
        for filename in special_files:
            (temp_dir / filename).write_text("內容")
        
        scanner = FileScanner(str(temp_dir))
        result = scanner.scan_directory()
        
        assert len(result) == len(special_files)
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_scan_zero_byte_files(self, temp_dir):
        """測試零位元組檔案"""
        zero_file = temp_dir / "zero.txt"
        zero_file.touch()  # 建立空檔案
        
        scanner = FileScanner(str(temp_dir))
        result = scanner.scan_directory()
        
        assert len(result) == 1
        assert str(zero_file) in result
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_scan_hidden_files(self, temp_dir):
        """測試隱藏檔案處理"""
        # 建立隱藏檔案
        hidden_file = temp_dir / ".hidden.txt"
        hidden_file.write_text("隱藏內容")
        
        normal_file = temp_dir / "normal.txt"
        normal_file.write_text("一般內容")
        
        scanner = FileScanner(str(temp_dir))
        result = scanner.scan_directory()
        
        # 應該跳過隱藏檔案
        assert len(result) == 1
        assert str(normal_file) in result
        assert str(hidden_file) not in result
    
    @pytest.mark.unit
    @pytest.mark.scanner
    @pytest.mark.slow
    def test_scan_large_directory(self, large_file_set):
        """測試大量檔案掃描"""
        scanner = FileScanner(str(large_file_set))
        result = scanner.scan_directory()
        
        assert len(result) == 100
        
        # 驗證所有檔案都被找到
        for i in range(100):
            expected_file = str(large_file_set / f"file_{i:03d}.txt")
            assert expected_file in result
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_scan_with_symlinks(self, temp_dir):
        """測試符號連結處理"""
        # 建立實際檔案
        actual_file = temp_dir / "actual.txt"
        actual_file.write_text("實際內容")
        
        # 建立符號連結（如果系統支援）
        try:
            symlink = temp_dir / "link.txt"
            symlink.symlink_to(actual_file)
            
            scanner = FileScanner(str(temp_dir))
            result = scanner.scan_directory()
            
            # 應該找到兩個檔案（實際檔案和符號連結）
            assert len(result) == 2
        except OSError:
            # Windows 可能需要管理員權限
            pytest.skip("系統不支援符號連結")
    
    @pytest.mark.unit
    @pytest.mark.scanner
    @pytest.mark.parametrize("depth,expected_count", [
        (0, 1),   # 只掃描根目錄
        (1, 2),   # 掃描到第一層
        (2, 3),   # 掃描到第二層
        (None, 4) # 無限深度
    ])
    def test_depth_limit_variations(self, nested_directory_structure, depth, expected_count):
        """測試不同深度限制的變化"""
        scanner = FileScanner(str(nested_directory_structure), max_depth=depth)
        result = scanner.scan_directory()
        
        # 根據深度限制，應該找到不同數量的檔案
        assert len(result) == expected_count


class TestScannerHelpers:
    """Scanner 輔助函數測試"""
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_get_file_info(self, sample_text_file):
        """測試獲取檔案資訊"""
        info = get_file_info(sample_text_file)
        
        assert info["name"] == "sample.txt"
        assert info["path"] == str(sample_text_file)
        assert info["size"] > 0
        assert info["extension"] == ".txt"
        assert "modified_time" in info
        assert "created_time" in info
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_get_file_info_nonexistent(self):
        """測試獲取不存在檔案的資訊"""
        info = get_file_info(Path("/不存在的檔案.txt"))
        
        assert info["name"] == "不存在的檔案.txt"
        assert info["size"] == 0
        assert info["error"] is not None
    
    @pytest.mark.unit
    @pytest.mark.scanner
    def test_save_scan_result(self, temp_dir, mock_file_paths_data):
        """測試儲存掃描結果"""
        output_file = temp_dir / "scan_result.json"
        save_scan_result(mock_file_paths_data, str(output_file))
        
        assert output_file.exists()
        
        # 驗證儲存的內容
        import json
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == mock_file_paths_data