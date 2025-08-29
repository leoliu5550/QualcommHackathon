"""Parser management and factory system.

Handles parser registration and file format detection.
Automatically loads appropriate parsers for different file types.
"""

from fileorg.parsers.base import BaseParser, ParseResult
from pathlib import Path
from typing import List, Optional


class ParserFactory:
    """Factory for creating file parsers.
    
    Manages parser registration and instantiation.
    Supports dynamic parser loading and custom formats.
    """

    # 空的解析器映射，所有解析器都需要註冊
    _parsers = {}
    _initialized = False

    @classmethod
    def _initialize_default_parsers(cls):
        """Load default parsers on first use.
        
        Lazy loading prevents circular imports.
        """
        if not cls._initialized:
            # Import all available parsers
            from fileorg.parsers.txt_parser import TxtParser
            from fileorg.parsers.json_parser import JsonParser
            from fileorg.parsers.csv_parser import CsvParser
            from fileorg.parsers.html_parser import HtmlParser
            from fileorg.parsers.md_parser import MarkdownParser
            from fileorg.parsers.pdf_parser import PdfParser
            from fileorg.parsers.word_parser import DocxParser
            from fileorg.parsers.ppt_parser import PptxParser
            from fileorg.parsers.xlsx_parser import XlsxParser
            from fileorg.parsers.xml_parser import XmlParser

            # Register all parsers
            cls._parsers[".txt"] = TxtParser
            cls._parsers[".json"] = JsonParser
            cls._parsers[".csv"] = CsvParser
            cls._parsers[".html"] = HtmlParser
            cls._parsers[".htm"] = HtmlParser
            cls._parsers[".md"] = MarkdownParser
            cls._parsers[".markdown"] = MarkdownParser
            cls._parsers[".pdf"] = PdfParser
            cls._parsers[".docx"] = DocxParser
            cls._parsers[".doc"] = DocxParser
            cls._parsers[".pptx"] = PptxParser
            cls._parsers[".ppt"] = PptxParser
            cls._parsers[".xlsx"] = XlsxParser
            cls._parsers[".xls"] = XlsxParser
            cls._parsers[".xml"] = XmlParser
            cls._initialized = True

    @classmethod
    def create_parser(cls, file_extension: str, char_limit: int = 1000) -> Optional[BaseParser]:
        """Create parser for given file extension.

        Args:
            file_extension: File extension (e.g., '.txt')
            char_limit: Maximum characters to extract

        Returns:
            Parser instance or None if unsupported
        """
        cls._initialize_default_parsers()
        if file_extension and not file_extension.startswith("."):
            file_extension = "." + file_extension

        parser_class = cls._parsers.get(file_extension.lower())
        if parser_class:
            return parser_class(char_limit)
        return None

    @classmethod
    def register_parser(cls, file_extension: str, parser_class: type):
        """Register a parser for a file type.

        Args:
            file_extension: File extension to handle
            parser_class: Parser class to use
        """
        cls._parsers[file_extension.lower()] = parser_class

    @classmethod
    def unregister_parser(cls, file_extension: str):
        """Remove a registered parser.

        Args:
            file_extension: File extension to remove
        """
        cls._parsers.pop(file_extension.lower(), None)

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of supported file extensions.
        
        Returns:
            List of extensions like ['.txt', '.pdf', ...]
        """
        cls._initialize_default_parsers()
        return list(cls._parsers.keys())

    @classmethod
    def is_supported(cls, file_extension: str) -> bool:
        """Check if file type is supported.
        
        Args:
            file_extension: Extension to check
            
        Returns:
            True if parser available for this type
        """
        cls._initialize_default_parsers()
        if file_extension and not file_extension.startswith("."):
            file_extension = "." + file_extension
        return file_extension.lower() in cls._parsers


class FileParserManager:
    """High-level interface for file parsing.
    
    Simplifies parsing single or multiple files.
    Handles errors and unsupported formats gracefully.
    """

    def __init__(self, char_limit: int = 1000, auto_register_defaults: bool = True):
        """Initialize parser manager.
        
        Args:
            char_limit: Maximum characters per file
            auto_register_defaults: Load default parsers
        """
        self.char_limit = char_limit

    def parse_file(self, file_path: str) -> ParseResult:
        """Parse a single file.

        Args:
            file_path: Path to file

        Returns:
            ParseResult with content or error
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return ParseResult(
                success=False, error=f"File not found: {file_path}", file_path=str(file_path)
            )

        file_extension = file_path.suffix.lower()
        parser = ParserFactory.create_parser(file_extension, self.char_limit)

        if parser is None:
            return ParseResult(
                success=False, error=f"Unsupported format: {file_extension}", file_path=str(file_path)
            )

        result = parser.parse(file_path)
        result.file_path = str(file_path)
        return result

    def parse_multiple_files(self, file_paths: List[str]) -> List[ParseResult]:
        """Parse multiple files in batch.

        Args:
            file_paths: List of file paths

        Returns:
            List of ParseResults for each file
        """
        results = []
        for file_path in file_paths:
            result = self.parse_file(file_path)
            results.append(result)
        return results

    def get_supported_formats(self) -> List[str]:
        """Get supported file formats.
        
        Returns:
            List of supported extensions
        """
        return ParserFactory.get_supported_extensions()

    def register_custom_parser(self, file_extension: str, parser_class: type):
        """Register custom parser.

        Args:
            file_extension: Extension to handle
            parser_class: Parser class to register
        """
        ParserFactory.register_parser(file_extension, parser_class)
