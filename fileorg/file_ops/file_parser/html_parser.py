# html_parser.py
from pathlib import Path

import chardet
from bs4 import BeautifulSoup

from fileorg.file_ops.ports import IParser, ParserOutput


class HtmlParser(IParser):
    """Parser for HTML (.html, .htm) files with encoding detection and text extraction."""

    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding for proper reading of multi-byte text."""
        with open(file_path, "rb") as f:
            raw = f.read(4096)  # 讀前4KB作為樣本
        detected = chardet.detect(raw)
        encoding = detected.get("encoding") or "utf-8"
        encoding = encoding.lower()
        if "big5" in encoding:
            return "big5"
        elif "gb" in encoding:
            return "gb18030"
        return encoding

    def _truncate_content(self, content: str, char_limit: int) -> str:
        """Truncate content if it exceeds character limit."""
        if len(content) > char_limit:
            return content[:char_limit]
        return content

    def parse(self, file_path: Path, char_limit: int) -> ParserOutput:
        """Parse an HTML file, extract text content, handle encoding, and truncate if needed."""
        try:
            encoding = self._detect_encoding(file_path)
            with open(file_path, "r", encoding=encoding, errors="ignore") as f:
                html = f.read()

            # 使用 BeautifulSoup 提取純文字
            soup = BeautifulSoup(html, "html.parser")
            text_content = soup.get_text(separator="\n", strip=True)

            truncated_content = self._truncate_content(text_content, char_limit)

            return ParserOutput(success=True, content=truncated_content, error="")
        except Exception as e:
            return ParserOutput(success=False, content="", error=str(e))
