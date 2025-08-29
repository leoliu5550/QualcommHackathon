"""JSON file parser for structured data extraction.

Handles JSON documents with pretty printing for readability.
Falls back to plain text if JSON structure is invalid.
"""

from fileorg.parsers.base import BaseParser, ParseResult
from pathlib import Path
import json


class JsonParser(BaseParser):
    """Parser for JSON data files.
    
    Extracts and formats JSON content for analysis.
    Gracefully handles malformed JSON by treating as text.
    """

    def parse(self, file_path: Path) -> ParseResult:
        """Extract content from JSON file.
        
        Attempts to parse as JSON first, falls back to plain text.
        Formats JSON with indentation for better readability.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            ParseResult with formatted JSON or raw text
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            content = json.dumps(data, ensure_ascii=False, indent=2)
            truncated_content, is_truncated = self._truncate_content(content)

            return ParseResult(
                success=True,
                content=truncated_content,
                file_type="json",
                original_length=len(content),
                truncated=is_truncated,
            )
        except Exception as e:
            # Try to read as plain text if JSON parsing fails
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                truncated_content, is_truncated = self._truncate_content(content)
                return ParseResult(
                    success=True,
                    content=truncated_content,
                    file_type="json",
                    original_length=len(content),
                    truncated=is_truncated,
                    error=f"JSON parsing error: {str(e)}",
                )
            except Exception as read_error:
                return ParseResult(success=False, file_type="json", error=str(read_error))
