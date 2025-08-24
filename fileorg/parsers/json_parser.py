from fileorg.parsers.base import BaseParser, ParseResult
from pathlib import Path
import json

class JsonParser(BaseParser):
    """JSON 檔案解析器"""
    
    def parse(self, file_path: Path) -> ParseResult:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            content = json.dumps(data, ensure_ascii=False, indent=2)
            truncated_content, is_truncated = self._truncate_content(content)
            
            return ParseResult(
                success=True,
                content=truncated_content,
                file_type='json',
                original_length=len(content),
                truncated=is_truncated
            )
        except Exception as e:
            return ParseResult(success=False, error=str(e))