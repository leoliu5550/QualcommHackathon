"""Parser management and factory system.

Handles parser registration and file format detection.
Automatically loads appropriate parsers for different file types.
"""

# from pathlib import Path
# from typing import List, Optional, Type

# from fileorg.file_ops.ports import IParser, ParserOutput


# class ParserFactory:
#     """Factory for creating parsers dynamically (manages adapters)."""

#     _parsers: dict[str, Type[IParser]] = {}

#     @classmethod
#     def register_parser(cls, file_extension: str, parser_class: Type[IParser]):
#         cls._parsers[file_extension.lower()] = parser_class

#     @classmethod
#     def create_parser(cls, file_extension: str) -> Optional[IParser]:
#         parser_class = cls._parsers.get(file_extension.lower())
#         if parser_class:
#             return parser_class()
#         return None

#     @classmethod
#     def get_supported_extensions(cls) -> List[str]:
#         return list(cls._parsers.keys())


# class ParserManager:
#     """Hexagonal Application Service: orchestrates parsing through factory."""

#     def __init__(self, char_limit: int = 1000):
#         self.char_limit = char_limit

#     def parse_file(self, file_path: str) -> ParserOutput:
#         path = Path(file_path)
#         if not path.exists():
#             return ParserOutput(success=False, content="", is_truncated=False, error="File not found")

#         parser = ParserFactory.create_parser(path.suffix)
#         if parser is None:
#             return ParserOutput(success=False, content="", is_truncated=False, error="Unsupported file type")

#         return parser.parse(path, self.char_limit)

#     def parse_multiple_files(self, file_paths: List[str]) -> List[ParserOutput]:
#         return [self.parse_file(fp) for fp in file_paths]

#     def register_custom_parser(self, file_extension: str, parser_class: Type[IParser]):
#         ParserFactory.register_parser(file_extension, parser_class)

#     def get_supported_formats(self) -> List[str]:
#         return ParserFactory.get_supported_extensions()
