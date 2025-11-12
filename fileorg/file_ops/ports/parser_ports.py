from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


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


class MultiParserOutput(Dict[str, str]):
    """
    Represents a mapping from file paths to their parsed text content.

    This class is a dictionary subclass where:
    - **Key**: Absolute file path (from ScanOutput.path)
    - **Value**: Extracted text content (from ParserOutput.content, only for successful parses)

    It is intended to store the output of the file parsing stage in a format
    suitable for downstream processing (e.g., feeding into an LLM).

    Example:
        >>> output = MultiParserOutput()
        >>> output["/home/user/docs/report.pdf"] = "First quarter sales report..."
        >>> output["/home/user/docs/report.pdf"]
        'First quarter sales report...'

    Notes:
        - Only include files where parsing succeeded (ParserOutput.success == True).
        - Can be used and accessed like a normal Python dictionary.
    """

    pass


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
