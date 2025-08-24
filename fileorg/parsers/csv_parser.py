from fileorg.parsers.base import BaseParser, ParseResult
from pathlib import Path
import csv

class CsvParser(BaseParser):
    """CSV 檔案解析器"""
    
    def parse(self, file_path: Path) -> ParseResult:
        try:
            content = ""
            encodings = ['utf-8', 'big5', 'gbk', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, newline='') as file:
                        csv_reader = csv.reader(file)
                        row_count = 0
                        
                        for row in csv_reader:
                            row_text = ",".join(row) + "\n"
                            content += row_text
                            row_count += 1
                            
                            if len(content) > self.char_limit or row_count > 100:
                                break
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise UnicodeDecodeError("無法以任何編碼讀取 CSV 檔案")
            
            truncated_content, is_truncated = self._truncate_content(content)
            
            return ParseResult(
                success=True,
                content=truncated_content,
                file_type='csv',
                original_length=len(content),
                truncated=is_truncated
            )
        except Exception as e:
            return ParseResult(success=False, error=str(e))
