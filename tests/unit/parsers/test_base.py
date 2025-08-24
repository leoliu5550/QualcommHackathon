"""
Base Parser 測試
"""
import pytest
from fileorg.parsers.base import BaseParser, ParseResult


class TestParseResult:
    """ParseResult 類別測試"""
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_result_creation(self):
        """測試 ParseResult 建立"""
        result = ParseResult(
            success=True,
            content="測試內容",
            file_type="txt",
            original_length=100,
            truncated=False,
            error="",
            file_path="/test/file.txt"
        )
        
        assert result.success is True
        assert result.content == "測試內容"
        assert result.file_type == "txt"
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
            file_type="txt"
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['success'] is True
        assert result_dict['content'] == "內容"
        assert result_dict['file_type'] == "txt"
    
    @pytest.mark.unit
    def test_parse_result_defaults(self):
        """測試 ParseResult 預設值"""
        result = ParseResult()
        
        assert result.success is False
        assert result.content == ""
        assert result.file_type == ""
        assert result.original_length == 0
        assert result.truncated is False
        assert result.error == ""
        assert result.file_path == ""
    
    @pytest.mark.unit
    def test_parse_result_partial_creation(self):
        """測試 ParseResult 部分參數建立"""
        result = ParseResult(
            success=True,
            content="test content"
        )
        
        assert result.success is True
        assert result.content == "test content"
        # 其他應該是預設值
        assert result.file_type == ""
        assert result.original_length == 0
        assert result.error == ""
    
    @pytest.mark.unit
    def test_parse_result_string_representation(self):
        """測試 ParseResult 字串表示"""
        result = ParseResult(
            success=True,
            content="test",
            file_type="txt"
        )
        
        str_repr = str(result)
        assert "success" in str_repr.lower()
        assert "txt" in str_repr


class TestBaseParser:
    """BaseParser 基礎類別測試"""
    
    @pytest.mark.unit
    def test_base_parser_initialization(self):
        """測試 BaseParser 初始化"""
        parser = BaseParser(char_limit=1000)
        
        assert parser.char_limit == 1000
    
    @pytest.mark.unit
    def test_base_parser_default_char_limit(self):
        """測試 BaseParser 預設字元限制"""
        parser = BaseParser()
        
        # 應該有合理的預設值
        assert hasattr(parser, 'char_limit')
        assert parser.char_limit > 0
    
    @pytest.mark.unit
    def test_base_parser_parse_not_implemented(self):
        """測試 BaseParser parse 方法未實作"""
        parser = BaseParser()
        
        with pytest.raises(NotImplementedError):
            parser.parse("/test/file.txt")
    
    @pytest.mark.unit
    def test_base_parser_custom_char_limit(self):
        """測試 BaseParser 自訂字元限制"""
        custom_limits = [100, 500, 1500, 5000]
        
        for limit in custom_limits:
            parser = BaseParser(char_limit=limit)
            assert parser.char_limit == limit
    
    @pytest.mark.unit
    def test_base_parser_zero_char_limit(self):
        """測試 BaseParser 零字元限制"""
        parser = BaseParser(char_limit=0)
        assert parser.char_limit == 0
    
    @pytest.mark.unit
    def test_base_parser_negative_char_limit(self):
        """測試 BaseParser 負數字元限制"""
        # 應該接受負數但可能在實際使用時有特殊處理
        parser = BaseParser(char_limit=-1)
        assert parser.char_limit == -1


class TestBaseParserExtended:
    """BaseParser 擴展測試"""
    
    @pytest.mark.unit
    def test_base_parser_subclass_implementation(self):
        """測試 BaseParser 子類別實作"""
        class TestParser(BaseParser):
            def parse(self, file_path):
                return ParseResult(
                    success=True,
                    content=f"Parsed {file_path}",
                    file_type="test"
                )
        
        parser = TestParser(char_limit=100)
        result = parser.parse("/test/file.txt")
        
        assert result.success is True
        assert result.content == "Parsed /test/file.txt"
        assert result.file_type == "test"
        assert parser.char_limit == 100
    
    @pytest.mark.unit
    def test_base_parser_multiple_inheritance(self):
        """測試 BaseParser 多重繼承"""
        class Mixin:
            def extra_method(self):
                return "mixin method"
        
        class TestParser(BaseParser, Mixin):
            def parse(self, file_path):
                return ParseResult(success=True, content="test")
        
        parser = TestParser()
        
        # 應該同時擁有兩個類別的功能
        assert hasattr(parser, 'char_limit')
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'extra_method')
        assert parser.extra_method() == "mixin method"
    
    @pytest.mark.unit
    def test_base_parser_method_override(self):
        """測試 BaseParser 方法覆寫"""
        class TestParser(BaseParser):
            def __init__(self, char_limit=1000, extra_param="default"):
                super().__init__(char_limit)
                self.extra_param = extra_param
            
            def parse(self, file_path):
                return ParseResult(
                    success=True,
                    content=f"Parsed with {self.extra_param}",
                    file_type="test"
                )
        
        parser = TestParser(char_limit=500, extra_param="custom")
        result = parser.parse("/test/file.txt")
        
        assert parser.char_limit == 500
        assert parser.extra_param == "custom"
        assert result.content == "Parsed with custom"
    
    @pytest.mark.unit
    def test_base_parser_error_handling(self):
        """測試 BaseParser 錯誤處理"""
        class ErrorParser(BaseParser):
            def parse(self, file_path):
                if file_path == "/error/file.txt":
                    return ParseResult(
                        success=False,
                        error="Simulated parsing error",
                        file_path=file_path
                    )
                return ParseResult(success=True, content="ok")
        
        parser = ErrorParser()
        
        # 正常情況
        result_ok = parser.parse("/ok/file.txt")
        assert result_ok.success is True
        assert result_ok.error == ""
        
        # 錯誤情況
        result_error = parser.parse("/error/file.txt")
        assert result_error.success is False
        assert result_error.error == "Simulated parsing error"
        assert result_error.file_path == "/error/file.txt"


class TestParseResultAdvanced:
    """ParseResult 進階測試"""
    
    @pytest.mark.unit
    def test_parse_result_equality(self):
        """測試 ParseResult 相等性比較"""
        result1 = ParseResult(
            success=True,
            content="test",
            file_type="txt"
        )
        
        result2 = ParseResult(
            success=True,
            content="test",
            file_type="txt"
        )
        
        result3 = ParseResult(
            success=True,
            content="different",
            file_type="txt"
        )
        
        # 如果實作了 __eq__ 方法
        if hasattr(result1, '__eq__'):
            assert result1 == result2
            assert result1 != result3
    
    @pytest.mark.unit
    def test_parse_result_serialization(self):
        """測試 ParseResult 序列化"""
        import json
        
        result = ParseResult(
            success=True,
            content="測試內容",
            file_type="txt",
            original_length=10,
            truncated=False
        )
        
        # 測試 JSON 序列化
        result_dict = result.to_dict()
        json_str = json.dumps(result_dict, ensure_ascii=False)
        
        # 反序列化
        deserialized = json.loads(json_str)
        
        assert deserialized['success'] is True
        assert deserialized['content'] == "測試內容"
        assert deserialized['file_type'] == "txt"
        assert deserialized['original_length'] == 10
        assert deserialized['truncated'] is False
    
    @pytest.mark.unit
    def test_parse_result_unicode_content(self):
        """測試 ParseResult Unicode 內容處理"""
        unicode_content = "測試 🎉 émojis and special chars: αβγ"
        
        result = ParseResult(
            success=True,
            content=unicode_content,
            file_type="txt"
        )
        
        assert result.content == unicode_content
        
        # 測試字典轉換保持 Unicode
        result_dict = result.to_dict()
        assert result_dict['content'] == unicode_content
    
    @pytest.mark.unit
    def test_parse_result_large_content(self):
        """測試 ParseResult 大內容處理"""
        large_content = "x" * 100000  # 100K characters
        
        result = ParseResult(
            success=True,
            content=large_content,
            file_type="txt",
            original_length=100000
        )
        
        assert len(result.content) == 100000
        assert result.original_length == 100000
        
        # 字典轉換應該正常工作
        result_dict = result.to_dict()
        assert len(result_dict['content']) == 100000