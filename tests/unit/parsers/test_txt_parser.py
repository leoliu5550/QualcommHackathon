"""
TXT Parser 測試
"""
import pytest
from fileorg.parsers.txt_parser import TxtParser


class TestTxtParser:
    """TxtParser 測試"""
    
    @pytest.mark.unit
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
    def test_txt_parser_basic_functionality(self, temp_dir):
        """測試 TXT 解析器基本功能"""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("Hello World\nSecond Line")
        
        parser = TxtParser(char_limit=1000)
        result = parser.parse(str(txt_file))
        
        assert result.success is True
        assert result.content == "Hello World\nSecond Line"
        assert result.file_type == "txt"
    
    @pytest.mark.unit
    def test_txt_parser_char_limit(self, temp_dir):
        """測試字元限制"""
        txt_file = temp_dir / "long.txt"
        long_content = "A" * 1000
        txt_file.write_text(long_content)
        
        parser = TxtParser(char_limit=100)
        result = parser.parse(str(txt_file))
        
        assert result.success is True
        assert len(result.content) == 100
        assert result.truncated is True
        assert result.original_length == 1000