"""提供檔案解析功能, 目前支持txt、pdf、docx、md、json、csv格式文件"""
from lib.file_parser.parser_manager import FileParserManager
from lib.file_parser.txt_parser import TxtParser
from lib.file_parser.pdf_parser import PdfParser
from lib.file_parser.word_parser import DocxParser
from lib.file_parser.md_parser import MarkdownParser
from lib.file_parser.json_parser import JsonParser
from lib.file_parser.csv_parser import CsvParser
from lib.file_parser.html_parser import HtmlParser
from lib.file_parser.ppt_parser import PptxParser
from lib.file_parser.xlsx_parser import XlsxParser
from lib.file_parser.xml_parser import XmlParser

# 創建管理器
parser_manager = FileParserManager(char_limit=400)
parser_manager.register_custom_parser('.csv', CsvParser)
parser_manager.register_custom_parser('.docx', DocxParser)
parser_manager.register_custom_parser('.pdf', PdfParser)
parser_manager.register_custom_parser('.md', MarkdownParser)
parser_manager.register_custom_parser('.json', JsonParser)
parser_manager.register_custom_parser('.txt', TxtParser)
parser_manager.register_custom_parser('.html', HtmlParser)
parser_manager.register_custom_parser('.htm', HtmlParser)
parser_manager.register_custom_parser('.pptx', PptxParser)
parser_manager.register_custom_parser('.xlsx', XlsxParser)
parser_manager.register_custom_parser('.xml', XmlParser)

# 用法範例


# """示範使用方法"""

# # 創建檔案解析管理器
# parser_manager = FileParserManager(char_limit=1000)

# print("支援的檔案格式:", parser_manager.get_supported_formats())

# # 解析單個檔案
# result = parser_manager.parse_file('example.txt')

# if result.success:
#     print(f"檔案類型: {result.file_type}")
#     print(f"原始長度: {result.original_length} 字符")
#     print(f"是否截斷: {result.truncated}")
#     print(f"內容預覽:\n{result.content}")
# else:
#     print(f"解析失敗: {result.error}")

# # 批量解析
# file_list = ['file1.txt', 'file2.pdf', 'file3.docx']
# results = parser_manager.parse_multiple_files(file_list)

# for result in results:
#     print(f"\n檔案: {result.file_path}")
#     print(f"狀態: {'成功' if result.success else '失敗'}")
#     if result.success:
#         print(f"內容長度: {len(result.content)} 字符")
#     else:
#         print(f"錯誤: {result.error}")
