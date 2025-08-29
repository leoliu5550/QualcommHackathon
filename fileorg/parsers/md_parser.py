"""Markdown file parser for documentation extraction.

Handles Markdown documents, preserving formatting for analysis.
"""

from fileorg.parsers.base import BaseParser, ParseResult
from pathlib import Path


class MarkdownParser(BaseParser):
    """Parser for Markdown documentation files.
    
    Extracts Markdown content as-is for categorization.
    Handles various text encodings automatically.
    """

    def parse(self, file_path: Path) -> ParseResult:
        """Extract content from Markdown file.
        
        Args:
            file_path: Path to Markdown file
            
        Returns:
            ParseResult with Markdown text content
        """
        try:
            content = self._try_encodings(file_path)
            truncated_content, is_truncated = self._truncate_content(content)

            return ParseResult(
                success=True,
                content=truncated_content,
                file_type="md",
                original_length=len(content),
                truncated=is_truncated,
            )
        except Exception as e:
            return ParseResult(success=False, error=str(e))
