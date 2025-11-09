# pdf_parser.py
from pathlib import Path

import pdfplumber

from fileorg.file_ops.ports import IParser, ParserOutput


class PdfParser(IParser):
    """Parser for PDF (.pdf) files with text extraction and character truncation."""

    def _truncate_content(self, content: str, char_limit: int) -> str:
        """Truncate content if it exceeds character limit."""
        if len(content) > char_limit:
            return content[:char_limit]
        return content

    def parse(self, file_path: Path, char_limit: int) -> ParserOutput:
        """Parse a PDF file and extract text content."""
        try:
            all_text = []

            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    all_text.append(page_text)

            full_text = "\n".join(all_text)
            truncated_text = self._truncate_content(full_text, char_limit)

            return ParserOutput(success=True, content=truncated_text, error="")

        except Exception as e:
            return ParserOutput(success=False, content="", error=str(e))
