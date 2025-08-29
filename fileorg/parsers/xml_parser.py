"""XML file parser for structured data extraction.

Extracts text content from XML documents.
"""

from pathlib import Path
import xml.etree.ElementTree as ET
from fileorg.parsers.base import BaseParser, ParseResult


class XmlParser(BaseParser):
    """Parser for XML documents.
    
    Extracts all text content from XML elements.
    """

    def parse(self, file_path: Path) -> ParseResult:
        """Extract text from XML file.
        
        Args:
            file_path: Path to XML file
            
        Returns:
            ParseResult with extracted text
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            text_content = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_content.append(elem.text.strip())
                if elem.tail and elem.tail.strip():
                    text_content.append(elem.tail.strip())

            text = " ".join(text_content)
            truncated_content, is_truncated = self._truncate_content(text)

            return ParseResult(
                success=True,
                content=truncated_content,
                file_type="xml",
                original_length=len(text),
                truncated=is_truncated,
                file_path=str(file_path),
            )
        except Exception as e:
            return ParseResult(
                success=False, error=f"Failed to parse XML: {str(e)}", file_path=str(file_path)
            )
