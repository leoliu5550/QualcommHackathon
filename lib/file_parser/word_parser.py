from lib.file_parser.base_parser import BaseParser, ParseResult

from pathlib import Path
from docx import Document

class DocxParser(BaseParser):
    """DOCX 檔案解析器"""
    
    def parse(self, file_path: Path) -> ParseResult:
        if Document is None:
            return ParseResult(success=False, error="需要安裝 python-docx 套件來解析 DOCX 檔案")
        
        try:
            doc = Document(file_path)
            content = ""
            
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
                if len(content) > self.char_limit:
                    break
            
            truncated_content, is_truncated = self._truncate_content(content)
            
            return ParseResult(
                success=True,
                content=truncated_content,
                file_type='docx',
                original_length=len(content),
                truncated=is_truncated
            )
        except Exception as e:
            return ParseResult(success=False, error=str(e))
