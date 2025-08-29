"""Microsoft Word document parser.

Extracts text from DOCX files using python-docx library.
"""

from fileorg.parsers.base import BaseParser, ParseResult
from pathlib import Path
from docx import Document


class DocxParser(BaseParser):
    """Parser for Microsoft Word documents.
    
    Extracts paragraph text from DOCX files.
    Requires python-docx library.
    """

    def parse(self, file_path: Path) -> ParseResult:
        """Extract text from Word document.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            ParseResult with document text
        """
        if Document is None:
            return ParseResult(success=False, error="python-docx library required for DOCX parsing")

        try:
            doc = Document(file_path)
            content = ""

            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
                if len(content) > self.char_limit:
                    break

            truncated_content, is_truncated = self._truncate_content(content)

            return ParseResult(
                success=True,
                content=truncated_content,
                file_type="docx",
                original_length=len(content),
                truncated=is_truncated,
            )
        except Exception as e:
            return ParseResult(success=False, error=str(e))
