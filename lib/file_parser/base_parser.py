from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any  # 新增型別註解所需

# 解析結果封裝類，儲存解析後的資訊與狀態
class ParseResult:
    """解析結果封裝類
    用於儲存檔案解析後的各項資訊，例如是否成功、內容、檔案型態、原始長度、是否截斷、錯誤訊息與檔案路徑。
    """
    
    def __init__(self, success: bool, content: str = "", file_type: str = "", 
                original_length: int = 0, truncated: bool = False, 
                error: str = "", file_path: str = ""):
        # 解析是否成功
        self.success = success
        # 解析後的內容
        self.content = content
        # 檔案型態（副檔名等）
        self.file_type = file_type
        # 原始內容長度
        self.original_length = original_length
        # 是否有被截斷
        self.truncated = truncated
        # 錯誤訊息（若有）
        self.error = error
        # 檔案路徑
        self.file_path = file_path
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式，方便序列化或輸出。"""
        return {
            'success': self.success,
            'content': self.content,
            'file_type': self.file_type,
            'original_length': self.original_length,
            'truncated': self.truncated,
            'error': self.error,
            'file_path': self.file_path
        }

# 抽象解析器基類，所有解析器需繼承此類別
class BaseParser(ABC):
    """抽象解析器基類
    定義解析器的基本結構與共用方法，所有具體解析器需繼承並實作 parse 方法。
    """
    
    def __init__(self, char_limit: int = 1000):
        # 內容截斷的字元上限，預設 1000
        self.char_limit = char_limit
    
    @abstractmethod
    def parse(self, file_path: Path) -> ParseResult:
        """解析檔案的抽象方法，子類別需實作。"""
        pass
    
    def _truncate_content(self, content: str) -> tuple[str, bool]:
        """截斷內容到指定長度，回傳截斷後的內容與是否有截斷。"""
        if len(content) > self.char_limit:
            return content[:self.char_limit], True
        return content, False
    
    def _try_encodings(self, file_path: Path, encodings: List[str] = None) -> str:
        """嘗試多種編碼讀取文件，遇到編碼錯誤會自動切換編碼。
        若全部失敗則以 utf-8 並忽略錯誤讀取。
        """
        if encodings is None:
            # 常見中文與西文編碼
            encodings = ['utf-8', 'big5', 'gbk', 'cp1252']
        
        for encoding in encodings:
            try:
                # 嘗試以不同編碼讀取
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                # 若解碼失敗則嘗試下一個編碼
                continue
        
        # 如果所有編碼都失敗，使用 utf-8 並忽略錯誤
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()