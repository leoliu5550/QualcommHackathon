from fileorg.parsers.base import BaseParser, ParseResult
from pathlib import Path

class MarkdownParser(BaseParser):
    """Markdown 檔案解析器"""
    
    def parse(self, file_path: Path) -> ParseResult:
        try:
            content = self._try_encodings(file_path)
            truncated_content, is_truncated = self._truncate_content(content)
            
            return ParseResult(
                success=True,
                content=truncated_content,
                file_type='md',
                original_length=len(content),
                truncated=is_truncated
            )
        except Exception as e:
            return ParseResult(success=False, error=str(e))