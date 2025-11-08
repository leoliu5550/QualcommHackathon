"""CSV file parser for spreadsheet data extraction.

Handles comma-separated values with automatic encoding detection.
Extracts rows as text for AI analysis.
"""

import csv
from pathlib import Path

import chardet

from fileorg.file_ops.ports import IParser, ParserOutput


class CsvParser(IParser):
    """Parser for CSV files with robust encoding handling (UTF-8, Big5, GBK, etc.)."""

    def _detect_encoding(self, file_path: Path) -> str:
        """Detect encoding to handle Chinese and multi-byte characters."""
        with open(file_path, "rb") as f:
            raw = f.read(4096)
        encoding = chardet.detect(raw).get("encoding") or "utf-8"
        encoding = encoding.lower()
        if "big5" in encoding:
            return "big5"
        elif "gb" in encoding:
            return "gb18030"
        return encoding

    def _truncate_content(self, content: str, char_limit: int):
        """Truncate content if it exceeds the character limit."""
        if len(content) > char_limit:
            return content[:char_limit], True
        return content, False

    def parse(self, file_path: Path, char_limit: int) -> ParserOutput:
        """Extract content from CSV file with encoding detection and truncation."""
        try:
            encoding = self._detect_encoding(file_path)
            content = ""
            row_count = 0

            with open(file_path, "r", encoding=encoding, newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    row_text = ",".join(row) + "\n"
                    content += row_text
                    row_count += 1
                    if len(content) >= char_limit or row_count >= 100:
                        break

            truncated_content, is_truncated = self._truncate_content(content, char_limit)
            return ParserOutput(success=True, content=truncated_content, istruncated=is_truncated, error="")

        except UnicodeDecodeError as e:
            return ParserOutput(success=False, content="", istruncated=False, error=f"Encoding error: {e}")
        except Exception as e:
            return ParserOutput(success=False, content="", istruncated=False, error=f"CSV parsing failed: {e}")
