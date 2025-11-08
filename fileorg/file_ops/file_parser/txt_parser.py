from pathlib import Path

import chardet

from fileorg.file_ops.ports import IParser, ParserOutput


class TxtParser(IParser):
    """Parser for plain text (.txt) files with robust encoding detection."""

    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding for proper reading of Chinese / multi-byte text."""
        with open(file_path, "rb") as f:
            raw = f.read(4096)  # 讀前4KB作為樣本
        detected = chardet.detect(raw)
        encoding = detected.get("encoding") or "utf-8"
        encoding = encoding.lower()
        # 中文常見編碼
        if "big5" in encoding:
            return "big5"
        elif "gb" in encoding:
            return "gb18030"
        return encoding

    def _truncate_content(self, content: str, char_limit: int):
        """Truncate content if it exceeds character limit."""
        if len(content) > char_limit:
            return content[:char_limit], True
        return content, False

    def parse(self, file_path: Path, char_limit: int) -> ParserOutput:
        """Parse a plain text file, handle encoding, and truncate if needed."""
        try:
            encoding = self._detect_encoding(file_path)
            with open(file_path, "r", encoding=encoding, errors="ignore") as f:
                content = f.read()

            truncated_content, is_truncated = self._truncate_content(content, char_limit)

            # ✅ 使用 istruncated 和 error
            return ParserOutput(success=True, content=truncated_content, istruncated=is_truncated, error="")
        except Exception as e:
            return ParserOutput(success=False, content="", istruncated=False, error=str(e))
