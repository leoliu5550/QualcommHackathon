from typing import Dict, List, Optional, Type

from fileorg.file_ops.adapters.file_parser.csv_parser import CsvParser
from fileorg.file_ops.adapters.file_parser.excel_parser import ExcelParser
from fileorg.file_ops.adapters.file_parser.html_parser import HtmlParser
from fileorg.file_ops.adapters.file_parser.mhtml_parser import MhtmlParser
from fileorg.file_ops.adapters.file_parser.pdf_parser import PdfParser
from fileorg.file_ops.adapters.file_parser.ppt_parser import PptParser
from fileorg.file_ops.adapters.file_parser.txt_parser import TxtParser
from fileorg.file_ops.adapters.file_parser.word_parser import WordParser
from fileorg.file_ops.ports.parser_ports import IParser, IParserFactory


class ParserFactoryAdapter(IParserFactory):
    """Concrete implementation of IParserFactory.

    Responsible for managing parser registrations
    and returning the correct parser implementation
    based on file extension.
    """

    def __init__(self):
        self._parsers: Dict[str, Type[IParser]] = {}
        self._register_default_parsers()

    def _register_default_parsers(self):
        self.register_parser(".txt", TxtParser)
        self.register_parser(".json", TxtParser)
        self.register_parser(".md", TxtParser)
        self.register_parser(".csv", CsvParser)
        self.register_parser(".xlsx", ExcelParser)
        self.register_parser(".htm", HtmlParser)
        self.register_parser(".html", HtmlParser)
        self.register_parser(".mhtml", MhtmlParser)
        self.register_parser(".pdf", PdfParser)
        self.register_parser(".doc", WordParser)
        self.register_parser(".docx", WordParser)
        self.register_parser(".pptx", PptParser)

    def register_parser(self, extension: str, parser_class: Type[IParser]):
        """Register a new parser for a given extension."""
        self._parsers[extension.lower()] = parser_class

    def create_parser(self, file_extension: str) -> Optional[IParser]:
        """Instantiate parser for the specified file type."""
        parser_class = self._parsers.get(file_extension.lower())
        return parser_class() if parser_class else None

    def get_supported_extensions(self) -> List[str]:
        """List all supported parser extensions."""
        return sorted(self._parsers.keys())
