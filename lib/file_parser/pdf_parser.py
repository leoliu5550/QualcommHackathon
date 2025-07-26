from lib.file_parser.base_parser import BaseParser, ParseResult
from pathlib import Path
import PyPDF2

class PdfParser(BaseParser):
    """PDF 檔案解析器"""
    
    def parse(self, file_path: Path) -> ParseResult:
        if PyPDF2 is None:
            return ParseResult(success=False, error="需要安裝 PyPDF2 套件來解析 PDF 檔案")
        
        try:
            content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                max_pages = min(len(pdf_reader.pages), 10)
                
                for page_num in range(max_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    content += page_text + "\n"
                    
                    if len(content) > self.char_limit:
                        break
            
            truncated_content, is_truncated = self._truncate_content(content)
            
            return ParseResult(
                success=True,
                content=truncated_content,
                file_type='pdf',
                original_length=len(content),
                truncated=is_truncated
            )
        except Exception as e:
            return ParseResult(success=False, error=str(e))
