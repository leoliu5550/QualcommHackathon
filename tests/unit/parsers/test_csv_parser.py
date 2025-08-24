"""
CSV Parser 測試
"""
import pytest
from fileorg.parsers.csv_parser import CsvParser


class TestCsvParser:
    """CsvParser 測試"""
    
    @pytest.mark.unit
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
    
    @pytest.mark.unit
    def test_csv_parser_basic_functionality(self, temp_dir):
        """測試 CSV 解析器基本功能"""
        csv_file = temp_dir / "test.csv"
        csv_file.write_text("姓名,年齡,城市\n張三,25,台北\n李四,30,高雄")
        
        parser = CsvParser(char_limit=1000)
        result = parser.parse(str(csv_file))
        
        assert result.success is True
        assert "張三" in result.content
        assert "台北" in result.content
        assert result.file_type == "csv"