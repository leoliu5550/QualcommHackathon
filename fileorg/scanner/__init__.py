"""
文件掃描模組

這個模組提供文件掃描功能，包括：
- FileScanner: 主要的文件掃描器類別
- 相關的工具函數用於文件信息獲取和結果保存
"""

from fileorg.scanner.core import FileScanner
from fileorg.scanner.helpers import get_file_info, save_scan_result, print_scan_summary

__all__ = [
    'FileScanner',
    'get_file_info', 
    'save_scan_result',
    'print_scan_summary'
]

__version__ = '1.0.0'