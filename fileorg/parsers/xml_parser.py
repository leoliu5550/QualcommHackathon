from pathlib import Path
import xml.etree.ElementTree as ET
from fileorg.parsers.base import BaseParser, ParseResult


class XmlParser(BaseParser):
    """XML 檔案解析器"""

    def parse(self, file_path: Path) -> ParseResult:
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
                success=False, error=f"無法解析XML檔案: {str(e)}", file_path=str(file_path)
            )
