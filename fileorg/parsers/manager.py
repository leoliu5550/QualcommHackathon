from fileorg.parsers.base import BaseParser, ParseResult

from pathlib import Path
from typing import List, Optional

class ParserFactory:
    """解析器工廠類"""
    
    # 空的解析器映射，所有解析器都需要註冊
    _parsers = {}
    
    @classmethod
    def create_parser(cls, file_extension: str, char_limit: int = 1000) -> Optional[BaseParser]:
        """
        根據檔案副檔名創建對應的解析器
        
        Args:
            file_extension (str): 檔案副檔名（包含點號，如 '.txt'）
            char_limit (int): 字符限制數量
            
        Returns:
            BaseParser: 對應的解析器實例，如果不支援則返回 None
        """
        parser_class = cls._parsers.get(file_extension.lower())
        if parser_class:
            return parser_class(char_limit)
        return None
    
    @classmethod
    def register_parser(cls, file_extension: str, parser_class: type):
        """
        註冊解析器
        
        Args:
            file_extension (str): 檔案副檔名
            parser_class (type): 解析器類別
        """
        cls._parsers[file_extension.lower()] = parser_class
    
    @classmethod
    def unregister_parser(cls, file_extension: str):
        """
        取消註冊解析器
        
        Args:
            file_extension (str): 檔案副檔名
        """
        cls._parsers.pop(file_extension.lower(), None)
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """獲取支援的檔案副檔名列表"""
        return list(cls._parsers.keys())
    
    @classmethod
    def is_supported(cls, file_extension: str) -> bool:
        """檢查是否支援指定的檔案格式"""
        return file_extension.lower() in cls._parsers
    


class FileParserManager:
    """文件解析管理器"""
    
    def __init__(self, char_limit: int = 1000, auto_register_defaults: bool = True):
        self.char_limit = char_limit
    
    def parse_file(self, file_path: str) -> ParseResult:
        """
        解析單個檔案
        
        Args:
            file_path (str): 檔案路徑
            
        Returns:
            ParseResult: 解析結果
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return ParseResult(
                success=False,
                error=f'檔案不存在: {file_path}',
                file_path=str(file_path)
            )
        
        file_extension = file_path.suffix.lower()
        parser = ParserFactory.create_parser(file_extension, self.char_limit)
        
        if parser is None:
            return ParseResult(
                success=False,
                error=f'不支援的檔案格式: {file_extension}',
                file_path=str(file_path)
            )
        
        result = parser.parse(file_path)
        result.file_path = str(file_path)
        return result
    
    def parse_multiple_files(self, file_paths: List[str]) -> List[ParseResult]:
        """
        批量解析多個檔案
        
        Args:
            file_paths (List[str]): 檔案路徑列表
            
        Returns:
            List[ParseResult]: 解析結果列表
        """
        results = []
        for file_path in file_paths:
            result = self.parse_file(file_path)
            results.append(result)
        return results
    
    def get_supported_formats(self) -> List[str]:
        """獲取支援的檔案格式"""
        return ParserFactory.get_supported_extensions()
    
    def register_custom_parser(self, file_extension: str, parser_class: type):
        """
        註冊自定義解析器的便捷方法
        
        Args:
            file_extension (str): 檔案副檔名
            parser_class (type): 解析器類別
        """
        ParserFactory.register_parser(file_extension, parser_class)