"""PDF file parser for document text extraction.

Extracts text from PDF documents using pypdf library.
Limits to first 10 pages for efficiency.
"""

from fileorg.parsers.base import BaseParser, ParseResult
from pathlib import Path

try:
    from pypdf import PdfReader

    PYPDF_AVAILABLE = True
except ImportError:
    PdfReader = None
    PYPDF_AVAILABLE = False


class PdfParser(BaseParser):
    """Parser for PDF documents.
    
    Extracts text from PDFs for content analysis.
    Requires pypdf library for functionality.
    """

    def parse(self, file_path: Path) -> ParseResult:
        """Extract text from PDF file.
        
        Reads up to 10 pages or char_limit, whichever comes first.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            ParseResult with extracted text or error
        """
        if not PYPDF_AVAILABLE:
            return ParseResult(success=False, error="pypdf library required for PDF parsing")

        try:
            content = ""
            with open(file_path, "rb") as file:
                pdf_reader = PdfReader(file)
                max_pages = min(len(pdf_reader.pages), 10)

                for page_num in range(max_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    content += page_text + "\n"

                    if len(content) > self.char_limit:
                        break

            truncated_content, is_truncated = self._truncate_content(content)

            return ParseResult(
                success=True,
                content=truncated_content,
                file_type="pdf",
                original_length=len(content),
                truncated=is_truncated,
            )
        except Exception as e:
            return ParseResult(success=False, error=str(e))
