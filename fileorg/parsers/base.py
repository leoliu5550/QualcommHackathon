"""Base parser module for file content extraction.

Provides the foundation for all file parsers in the FileOrg system.
Each parser extracts meaningful content from different file types.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any


class ParseResult:
    """Container for parsed file results.
    
    Stores everything we extract from a file - content, metadata, and status.
    Makes it easy to handle both successful and failed parsing attempts.
    """

    def __init__(
        self,
        success: bool = False,
        content: str = "",
        file_type: str = "",
        original_length: int = 0,
        truncated: bool = False,
        error: str = "",
        file_path: str = "",
    ):
        """Initialize parse result with file information.
        
        Args:
            success: Whether parsing succeeded
            content: Extracted text content
            file_type: File extension or type
            original_length: Original content length before truncation
            truncated: Whether content was cut for size limits
            error: Error message if parsing failed
            file_path: Path to the parsed file
        """
        self.success = success
        self.content = content
        self.file_type = file_type
        self.original_length = original_length
        self.truncated = truncated
        self.error = error
        self.file_path = file_path

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization.
        
        Returns:
            Dict with all parse result fields
        """
        return {
            "success": self.success,
            "content": self.content,
            "file_type": self.file_type,
            "original_length": self.original_length,
            "truncated": self.truncated,
            "error": self.error,
            "file_path": self.file_path,
        }

    def __str__(self) -> str:
        """Human-readable representation of parse result."""
        return f"ParseResult(success={self.success}, file_type={self.file_type}, content_length={len(self.content)})"

    def __eq__(self, other) -> bool:
        """Check if two ParseResults are equal."""
        if not isinstance(other, ParseResult):
            return False
        return (
            self.success == other.success
            and self.content == other.content
            and self.file_type == other.file_type
            and self.original_length == other.original_length
            and self.truncated == other.truncated
            and self.error == other.error
            and self.file_path == other.file_path
        )


class BaseParser(ABC):
    """Abstract base for all file parsers.
    
    Defines the interface that all parsers must follow.
    Handles common tasks like content truncation and encoding detection.
    """

    def __init__(self, char_limit: int = 1000):
        """Initialize parser with character limit.
        
        Args:
            char_limit: Maximum characters to extract (prevents memory issues)
        """
        self.char_limit = char_limit

    @abstractmethod
    def parse(self, file_path: Path) -> ParseResult:
        """Extract content from a file.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            ParseResult with extracted content or error info
        """
        pass

    def _truncate_content(self, content: str) -> tuple[str, bool]:
        """Truncate content to character limit.
        
        Args:
            content: Text to potentially truncate
            
        Returns:
            Tuple of (truncated_content, was_truncated)
        """
        if len(content) > self.char_limit:
            return content[: self.char_limit], True
        return content, False

    def _try_encodings(self, file_path: Path, encodings: List[str] = None) -> str:
        """Try multiple encodings to read a file.
        
        Automatically handles different text encodings (UTF-8, Chinese, etc.).
        Falls back to UTF-8 with error ignoring if all encodings fail.
        
        Args:
            file_path: Path to file to read
            encodings: List of encodings to try (uses defaults if None)
            
        Returns:
            File content as string
        """
        if encodings is None:
            encodings = ["utf-8", "big5", "gbk", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read()
