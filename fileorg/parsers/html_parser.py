from pathlib import Path
from html.parser import HTMLParser
from fileorg.parsers.base import BaseParser, ParseResult


class HTMLParser_Custom(HTMLParser):
    """自訂 HTML Parser，用於提取純文字內容"""

    def __init__(self):
        super().__init__()
        self.text_content = []

    def handle_data(self, data):
        if data.strip():
            self.text_content.append(data.strip())


class HtmlParser(BaseParser):
    """HTML 檔案解析器"""

    def parse(self, file_path: Path) -> ParseResult:
        try:
            # 使用 BaseParser 提供的多編碼嘗試讀取
            content = self._try_encodings(file_path)

            # 使用自訂的 HTML Parser
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
                success=False, error=f"無法解析HTML檔案: {str(e)}", file_path=str(file_path)
            )
