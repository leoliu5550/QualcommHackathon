# mhtml_parser.py
import email
from pathlib import Path

import chardet
from bs4 import BeautifulSoup

from fileorg.file_ops.ports.parser_ports import IParser, ParserOutput


class MhtmlParser(IParser):
    """Parser for MHTML (.mht, .mhtml) files with text extraction."""

    def _detect_encoding(self, raw_bytes: bytes) -> str:
        """Detect encoding for proper text decoding."""
        detected = chardet.detect(raw_bytes[:4096])
        encoding = detected.get("encoding") or "utf-8"
        encoding = encoding.lower()
        if "big5" in encoding:
            return "big5"
        elif "gb" in encoding:
            return "gb18030"
        return encoding

    def _truncate_content(self, content: str, char_limit: int) -> str:
        if len(content) > char_limit:
            return content[:char_limit]
        return content

    def parse(self, file_path: Path, char_limit: int) -> ParserOutput:
        try:
            with open(file_path, "rb") as f:
                raw_bytes = f.read()

            # 用 email parser 處理 MHTML
            msg = email.message_from_bytes(raw_bytes)
            html_parts = []

            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    encoding = self._detect_encoding(payload)
                    html_text = payload.decode(encoding, errors="ignore")
                    html_parts.append(html_text)

            full_html = "\n".join(html_parts)
            soup = BeautifulSoup(full_html, "html.parser")
            text_content = soup.get_text(separator="\n", strip=True)
            truncated_content = self._truncate_content(text_content, char_limit)

            return ParserOutput(success=True, content=truncated_content, error="")

        except Exception as e:
            return ParserOutput(success=False, content="", error=str(e))
