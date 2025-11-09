"""
Parser management and factory system.

Handles parser registration and file format detection.
Automatically loads appropriate parsers for different file types.
"""

from pathlib import Path
from typing import List

from fileorg.file_ops.ports.parser_ports import IParserFactory, ParserOutput


class ParseFileClient:
    """Use case for parsing files using the injected parser factory."""

    def __init__(self, parser_factory: IParserFactory, char_limit: int = 1000):
        self.parser_factory = parser_factory
        self.char_limit = char_limit

    def parse(self, file_path: str | Path) -> ParserOutput:
        path = Path(file_path)
        if not path.exists():
            return ParserOutput(success=False, content="", error="File not found")

        parser = self.parser_factory.create_parser(path.suffix)
        if parser is None:
            return ParserOutput(success=False, content="", error=f"Unsupported file type: {path.suffix}")

        return parser.parse(path, self.char_limit)

    def parse_multiple(self, file_paths: List[str | Path]) -> List[ParserOutput]:
        return [self.parse(fp) for fp in file_paths]
