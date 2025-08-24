"""
JSON Parser 測試
"""
import pytest
from fileorg.parsers.json_parser import JsonParser


class TestJsonParser:
    """JsonParser 測試"""
    
    @pytest.mark.unit
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
    def test_json_parser_basic_functionality(self, temp_dir):
        """測試 JSON 解析器基本功能"""
        json_file = temp_dir / "test.json"
        json_file.write_text('{"name": "test", "value": 123}')
        
        parser = JsonParser(char_limit=1000)
        result = parser.parse(str(json_file))
        
        assert result.success is True
        assert "name" in result.content
        assert "test" in result.content
        assert result.file_type == "json"