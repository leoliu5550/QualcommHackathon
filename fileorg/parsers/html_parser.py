"""HTML file parser for web page content extraction.

Extracts clean text from HTML documents, removing all markup.
Useful for analyzing web content and documentation.
"""

from pathlib import Path
from html.parser import HTMLParser
from fileorg.parsers.base import BaseParser, ParseResult


class HTMLParser_Custom(HTMLParser):
    """Custom HTML parser that extracts text only.
    
    Strips all HTML tags and keeps just the readable content.
    """

    def __init__(self):
        """Initialize with empty text buffer."""
        super().__init__()
        self.text_content = []

    def handle_data(self, data):
        """Collect non-empty text data from HTML.
        
        Args:
            data: Text content between HTML tags
        """
        if data.strip():
            self.text_content.append(data.strip())


class HtmlParser(BaseParser):
    """Parser for HTML web documents.
    
    Extracts text content from HTML files for categorization.
    Handles various encodings automatically.
    """

    def parse(self, file_path: Path) -> ParseResult:
        """Extract text from HTML file.
        
        Removes all HTML tags and returns clean text.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            ParseResult with extracted text content
        """
        try:
            content = self._try_encodings(file_path)

            parser = HTMLParser_Custom()
            parser.feed(content)
            text = " ".join(parser.text_content)

            truncated_content, is_truncated = self._truncate_content(text)

            return ParseResult(
                success=True,
                content=truncated_content,
                file_type="html",
                original_length=len(text),
                truncated=is_truncated,
                file_path=str(file_path),
            )
        except Exception as e:
            return ParseResult(
                success=False, error=f"Failed to parse HTML: {str(e)}", file_path=str(file_path)
            )
