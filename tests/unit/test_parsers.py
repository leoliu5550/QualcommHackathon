"""
Parsers 模組單元測試
測試各種檔案格式的解析功能
"""
import pytest
from fileorg.parsers.manager import FileParserManager, ParserFactory
from fileorg.parsers.base import ParseResult
from fileorg.parsers.txt_parser import TxtParser
from fileorg.parsers.json_parser import JsonParser
from fileorg.parsers.csv_parser import CsvParser


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
        assert result.file_type == ".txt"
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
        assert result.file_type == ".json"
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_csv_file(self, parser_test_files):
        """測試解析 CSV 檔案"""
        manager = FileParserManager(char_limit=1000)
        result = manager.parse_file(str(parser_test_files['csv']))
        
        assert result.success is True
        assert "張三" in result.content
        assert "台北" in result.content
        assert result.file_type == ".csv"
    
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
        assert results[0].file_type == ".txt"
        assert results[1].file_type == ".json"
        assert results[2].file_type == ".csv"
    
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
        assert result.file_type == ".json"
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


class TestParserFactory:
    """ParserFactory 測試"""
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_create_parser(self):
        """測試建立解析器"""
        parser = ParserFactory.create_parser('.txt')
        assert parser is not None
        assert isinstance(parser, TxtParser)
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_register_custom_parser(self):
        """測試註冊自定義解析器"""
        # 建立自定義解析器
        class CustomParser:
            def __init__(self, char_limit=1000):
                self.char_limit = char_limit
        
        # 註冊
        ParserFactory.register_parser('.custom', CustomParser)
        
        # 驗證註冊成功
        assert ParserFactory.is_supported('.custom')
        parser = ParserFactory.create_parser('.custom')
        assert isinstance(parser, CustomParser)
        
        # 清理
        ParserFactory.unregister_parser('.custom')
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_get_supported_extensions(self):
        """測試獲取支援的副檔名"""
        extensions = ParserFactory.get_supported_extensions()
        
        assert isinstance(extensions, list)
        assert '.txt' in extensions
        assert '.json' in extensions
        assert '.csv' in extensions


class TestIndividualParsers:
    """個別解析器測試"""
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_txt_parser_encoding_fallback(self, temp_dir):
        """測試 TXT 解析器的編碼回退機制"""
        # 建立包含特殊字元的檔案
        special_file = temp_dir / "special.txt"
        content = "測試內容 with émojis 😀"
        special_file.write_text(content, encoding='utf-8')
        
        parser = TxtParser(char_limit=1000)
        result = parser.parse(special_file)
        
        assert result.success is True
        assert "測試內容" in result.content
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_json_parser_pretty_format(self, temp_dir):
        """測試 JSON 解析器的格式化功能"""
        json_file = temp_dir / "test.json"
        json_file.write_text('{"a":1,"b":{"c":2}}')
        
        parser = JsonParser(char_limit=1000)
        result = parser.parse(json_file)
        
        assert result.success is True
        # JSON 應該被格式化
        assert "a" in result.content
        assert "b" in result.content
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_csv_parser_with_headers(self, temp_dir):
        """測試 CSV 解析器處理表頭"""
        csv_file = temp_dir / "test.csv"
        csv_file.write_text("Name,Age,City\nAlice,25,NYC\nBob,30,LA")
        
        parser = CsvParser(char_limit=1000)
        result = parser.parse(csv_file)
        
        assert result.success is True
        assert "Alice" in result.content
        assert "NYC" in result.content
        assert "Bob" in result.content


class TestParseResult:
    """ParseResult 類別測試"""
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_result_creation(self):
        """測試 ParseResult 建立"""
        result = ParseResult(
            success=True,
            content="測試內容",
            file_type=".txt",
            original_length=100,
            truncated=False,
            error="",
            file_path="/test/file.txt"
        )
        
        assert result.success is True
        assert result.content == "測試內容"
        assert result.file_type == ".txt"
        assert result.original_length == 100
        assert result.truncated is False
        assert result.error == ""
        assert result.file_path == "/test/file.txt"
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_result_to_dict(self):
        """測試 ParseResult 轉換為字典"""
        result = ParseResult(
            success=True,
            content="內容",
            file_type=".txt"
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['success'] is True
        assert result_dict['content'] == "內容"
        assert result_dict['file_type'] == ".txt"