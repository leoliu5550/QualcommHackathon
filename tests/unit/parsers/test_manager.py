"""
Parsers Manager 模組單元測試
測試檔案解析管理器功能
"""
import pytest
from fileorg.parsers.manager import FileParserManager
from fileorg.parsers.base import ParseResult


class TestParserManager:
    """FileParserManager 測試"""
    
    # ==================== 正常測試案例 ====================
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_txt_file(self, parser_test_files):
        """測試解析 TXT 檔案"""
        manager = FileParserManager(char_limit=1000)
        result = manager.parse_file(str(parser_test_files['txt']))
        
        assert result.success is True
        assert result.content == "測試文字內容\n第二行"
        assert result.file_type == "txt"
        assert result.truncated is False
        assert result.error == ""
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_json_file(self, parser_test_files):
        """測試解析 JSON 檔案"""
        manager = FileParserManager(char_limit=1000)
        result = manager.parse_file(str(parser_test_files['json']))
        
        assert result.success is True
        assert "name" in result.content
        assert "測試" in result.content
        assert result.file_type == "json"
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_csv_file(self, parser_test_files):
        """測試解析 CSV 檔案"""
        manager = FileParserManager(char_limit=1000)
        result = manager.parse_file(str(parser_test_files['csv']))
        
        assert result.success is True
        assert "張三" in result.content
        assert "台北" in result.content
        assert result.file_type == "csv"
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_multiple_files(self, parser_test_files):
        """測試批量解析多個檔案"""
        manager = FileParserManager(char_limit=1000)
        file_paths = [
            str(parser_test_files['txt']),
            str(parser_test_files['json']),
            str(parser_test_files['csv'])
        ]
        
        results = manager.parse_multiple_files(file_paths)
        
        assert len(results) == 3
        assert all(isinstance(r, ParseResult) for r in results)
        assert results[0].file_type == "txt"
        assert results[1].file_type == "json"
        assert results[2].file_type == "csv"
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_char_limit_truncation(self, temp_dir):
        """測試字元限制截斷功能"""
        long_file = temp_dir / "long.txt"
        long_content = "x" * 2000
        long_file.write_text(long_content)
        
        manager = FileParserManager(char_limit=100)
        result = manager.parse_file(str(long_file))
        
        assert result.success is True
        assert result.truncated is True
        assert len(result.content) == 100
        assert result.original_length == 2000
    
    # ==================== 異常測試案例 ====================
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_nonexistent_file(self):
        """測試解析不存在的檔案"""
        manager = FileParserManager()
        result = manager.parse_file("/不存在的檔案.txt")
        
        assert result.success is False
        assert "檔案不存在" in result.error
        assert result.content == ""
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_unsupported_format(self, temp_dir):
        """測試不支援的檔案格式"""
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_text("內容")
        
        manager = FileParserManager()
        result = manager.parse_file(str(unsupported_file))
        
        assert result.success is False
        assert "不支援的檔案格式" in result.error
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_corrupted_json(self, temp_dir):
        """測試解析損壞的 JSON 檔案"""
        corrupted_json = temp_dir / "corrupted.json"
        corrupted_json.write_text("{invalid json content")
        
        manager = FileParserManager()
        result = manager.parse_file(str(corrupted_json))
        
        # 應該能讀取內容，但可能無法正確解析
        assert result.file_type == "json"
        # 內容應該被當作純文字處理
        assert "{invalid json content" in result.content
    
    # ==================== 邊緣測試案例 ====================
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_empty_file(self, temp_dir):
        """測試解析空檔案"""
        empty_file = temp_dir / "empty.txt"
        empty_file.touch()
        
        manager = FileParserManager()
        result = manager.parse_file(str(empty_file))
        
        assert result.success is True
        assert result.content == ""
        assert result.original_length == 0
        assert result.truncated is False
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_file_with_encoding_issues(self, temp_dir):
        """測試編碼問題的處理"""
        # 建立不同編碼的檔案
        encodings = [
            ('utf8_file.txt', 'utf-8', '這是UTF-8編碼'),
            ('big5_file.txt', 'big5', '這是Big5編碼'),
            ('gbk_file.txt', 'gbk', '这是GBK编码')
        ]
        
        for filename, encoding, content in encodings:
            file_path = temp_dir / filename
            file_path.write_text(content, encoding=encoding)
            
            manager = FileParserManager()
            result = manager.parse_file(str(file_path))
            
            # 應該能正確處理不同編碼
            assert result.success is True
            # 內容可能因編碼轉換而略有不同，但不應該失敗
    
    @pytest.mark.unit
    @pytest.mark.parser
    @pytest.mark.parametrize("char_limit,expected_length", [
        (10, 10),
        (50, 50),
        (100, 100),
        (1000, 200),  # 檔案只有200字元
    ])
    def test_various_char_limits(self, temp_dir, char_limit, expected_length):
        """測試不同的字元限制"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("x" * 200)
        
        manager = FileParserManager(char_limit=char_limit)
        result = manager.parse_file(str(test_file))
        
        assert result.success is True
        assert len(result.content) == min(expected_length, 200)


class TestParserManagerExtended:
    """FileParserManager 擴展測試"""
    
    @pytest.mark.unit
    def test_manager_initialization_defaults(self):
        """測試管理器預設初始化"""
        manager = FileParserManager()
        
        # 應該有合理的預設值
        assert hasattr(manager, 'char_limit')
        assert manager.char_limit > 0
    
    @pytest.mark.unit
    def test_manager_custom_char_limit(self):
        """測試自訂字元限制"""
        custom_limit = 500
        manager = FileParserManager(char_limit=custom_limit)
        
        assert manager.char_limit == custom_limit
    
    @pytest.mark.unit
    def test_parse_multiple_files_empty_list(self):
        """測試解析空檔案列表"""
        manager = FileParserManager()
        results = manager.parse_multiple_files([])
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    @pytest.mark.unit
    def test_parse_multiple_files_with_errors(self, parser_test_files, temp_dir):
        """測試解析包含錯誤檔案的列表"""
        manager = FileParserManager()
        
        # 混合有效和無效檔案
        file_paths = [
            str(parser_test_files['txt']),  # 有效
            "/nonexistent/file.txt",        # 無效
            str(parser_test_files['json'])   # 有效
        ]
        
        results = manager.parse_multiple_files(file_paths)
        
        assert len(results) == 3
        assert results[0].success is True   # 第一個成功
        assert results[1].success is False  # 第二個失敗
        assert results[2].success is True   # 第三個成功
    
    @pytest.mark.unit
    def test_manager_performance_large_batch(self, temp_dir):
        """測試管理器處理大批量檔案的效能"""
        import time
        
        # 建立多個測試檔案
        file_paths = []
        for i in range(20):
            file_path = temp_dir / f"file_{i}.txt"
            file_path.write_text(f"Content {i}")
            file_paths.append(str(file_path))
        
        manager = FileParserManager(char_limit=100)
        
        start_time = time.time()
        results = manager.parse_multiple_files(file_paths)
        end_time = time.time()
        
        # 驗證結果
        assert len(results) == 20
        assert all(r.success for r in results)
        
        # 效能應該合理（每個檔案平均不超過0.1秒）
        avg_time_per_file = (end_time - start_time) / 20
        assert avg_time_per_file < 0.1