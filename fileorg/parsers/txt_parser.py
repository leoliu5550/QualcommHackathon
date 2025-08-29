"""Plain text file parser.

Handles text files with automatic encoding detection.
"""

from fileorg.parsers.base import BaseParser, ParseResult
from pathlib import Path


class TxtParser(BaseParser):
    """Parser for plain text files.
    
    Reads text content with multi-encoding support.
    """

    def parse(self, file_path: Path) -> ParseResult:
        """Extract content from text file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            ParseResult with text content
        """
        try:
            content = self._try_encodings(file_path)
            truncated_content, is_truncated = self._truncate_content(content)

            return ParseResult(
                success=True,
                content=truncated_content,
                file_type="txt",
                original_length=len(content),
                truncated=is_truncated,
            )
        except Exception as e:
            return ParseResult(success=False, error=str(e))
