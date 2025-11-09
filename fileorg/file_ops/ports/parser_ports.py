from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ParserOutput:
    """
    Represents the result of a file parsing operation.

    This data class encapsulates whether parsing succeeded, the extracted text content,
    and any error or truncation status encountered during the process.

    Attributes:
        success (bool): Whether the parsing succeeded.
        content (str): The extracted text content. Empty if parsing failed.
        error (str): Error message if parsing failed, otherwise an empty string.
    """

    success: bool
    content: str
    error: str


class IParser(ABC):
    """Abstract base for all file parsers.

    Defines the interface that all parsers must follow.
    Handles common tasks like content truncation and encoding detection.
    """

    @abstractmethod
    def parse(self, file_path: Path, char_limit: int) -> ParserOutput:
        """Extract content from a file.

        Args:
            file_path: Path to the file to parse
            char_limit: Maximum characters to extract (prevents memory issues)

        Returns:
            ParseResult with extracted content or error info
        """
        pass


class IParserFactory(ABC):
    """Abstract factory for creating file parser instances.

    The application layer depends on this interface,
    while adapters implement it to provide concrete parsers.
    """

    @abstractmethod
    def create_parser(self, file_extension: str) -> Optional[IParser]:
        """Instantiate a parser for a given file extension."""
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Return all supported file extensions."""
        pass
