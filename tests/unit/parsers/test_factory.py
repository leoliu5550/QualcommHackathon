"""
Parser Factory 測試
"""
import pytest
from fileorg.parsers.manager import ParserFactory
from fileorg.parsers.txt_parser import TxtParser


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
    
    @pytest.mark.unit
    def test_factory_unsupported_extension(self):
        """測試不支援的副檔名"""
        parser = ParserFactory.create_parser('.unsupported')
        assert parser is None
    
    @pytest.mark.unit
    def test_factory_case_insensitive(self):
        """測試副檔名不區分大小寫"""
        parser_lower = ParserFactory.create_parser('.txt')
        parser_upper = ParserFactory.create_parser('.TXT')
        
        # 應該都能建立解析器
        assert parser_lower is not None
        assert parser_upper is not None
        assert type(parser_lower) is type(parser_upper)
    
    @pytest.mark.unit
    def test_factory_with_dot_prefix(self):
        """測試帶點和不帶點的副檔名"""
        parser_with_dot = ParserFactory.create_parser('.txt')
        parser_without_dot = ParserFactory.create_parser('txt')
        
        # 應該都能建立解析器
        assert parser_with_dot is not None
        assert parser_without_dot is not None
        assert type(parser_with_dot) is type(parser_without_dot)
    
    @pytest.mark.unit
    def test_factory_register_duplicate(self):
        """測試註冊重複的解析器"""
        class CustomParser1:
            def __init__(self, char_limit=1000):
                self.char_limit = char_limit
                self.type = "custom1"
        
        class CustomParser2:
            def __init__(self, char_limit=1000):
                self.char_limit = char_limit
                self.type = "custom2"
        
        try:
            # 註冊第一個解析器
            ParserFactory.register_parser('.test', CustomParser1)
            parser1 = ParserFactory.create_parser('.test')
            assert parser1.type == "custom1"
            
            # 註冊第二個解析器（覆蓋第一個）
            ParserFactory.register_parser('.test', CustomParser2)
            parser2 = ParserFactory.create_parser('.test')
            assert parser2.type == "custom2"
        
        finally:
            # 清理
            ParserFactory.unregister_parser('.test')
    
    @pytest.mark.unit
    def test_factory_unregister_nonexistent(self):
        """測試取消註冊不存在的解析器"""
        # 取消註冊不存在的解析器不應該出錯
        try:
            ParserFactory.unregister_parser('.nonexistent')
        except Exception:
            pytest.fail("Unregistering nonexistent parser should not raise exception")
    
    @pytest.mark.unit
    def test_factory_is_supported(self):
        """測試檢查是否支援特定副檔名"""
        # 測試已知支援的格式
        assert ParserFactory.is_supported('.txt') is True
        assert ParserFactory.is_supported('.json') is True
        
        # 測試不支援的格式
        assert ParserFactory.is_supported('.xyz') is False
        assert ParserFactory.is_supported('.unknown') is False
    
    @pytest.mark.unit
    def test_factory_extension_normalization(self):
        """測試副檔名正規化"""
        # 測試各種格式的副檔名
        test_cases = [
            '.txt',
            'txt',
            '.TXT',
            'TXT',
            '.Txt',
            'Txt'
        ]
        
        for ext in test_cases:
            parser = ParserFactory.create_parser(ext)
            assert parser is not None, f"Failed to create parser for extension: {ext}"
            assert isinstance(parser, TxtParser)


class TestParserFactoryAdvanced:
    """ParserFactory 進階測試"""
    
    @pytest.mark.unit
    def test_factory_thread_safety(self):
        """測試工廠的執行緒安全性"""
        import threading
        import time
        
        results = []
        
        def create_parsers():
            for _ in range(10):
                parser = ParserFactory.create_parser('.txt')
                results.append(parser is not None)
                time.sleep(0.01)  # 模擬處理時間
        
        # 建立多個執行緒
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_parsers)
            threads.append(thread)
            thread.start()
        
        # 等待所有執行緒完成
        for thread in threads:
            thread.join()
        
        # 驗證所有結果都是成功的
        assert len(results) == 50  # 5 threads * 10 parsers each
        assert all(results)
    
    @pytest.mark.unit
    def test_factory_memory_usage(self):
        """測試工廠的記憶體使用"""
        # 建立大量解析器實例
        parsers = []
        
        for _ in range(100):
            parser = ParserFactory.create_parser('.txt')
            parsers.append(parser)
        
        # 驗證所有解析器都建立成功
        assert len(parsers) == 100
        assert all(isinstance(p, TxtParser) for p in parsers)
        
        # 清理
        parsers.clear()
    
    @pytest.mark.unit
    def test_factory_custom_parser_inheritance(self):
        """測試自定義解析器的繼承"""
        from fileorg.parsers.base import BaseParser
        
        class InheritedParser(BaseParser):
            def __init__(self, char_limit=1000):
                super().__init__(char_limit)
                self.parser_type = "inherited"
            
            def parse(self, file_path):
                # 簡單的解析實現
                from fileorg.parsers.base import ParseResult
                return ParseResult(
                    success=True,
                    content="inherited content",
                    file_type="inherited"
                )
        
        try:
            # 註冊繼承的解析器
            ParserFactory.register_parser('.inherited', InheritedParser)
            
            # 驗證可以建立和使用
            parser = ParserFactory.create_parser('.inherited')
            assert isinstance(parser, InheritedParser)
            assert isinstance(parser, BaseParser)
            assert parser.parser_type == "inherited"
        
        finally:
            # 清理
            ParserFactory.unregister_parser('.inherited')