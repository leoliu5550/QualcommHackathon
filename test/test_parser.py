import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.file_parser import parser_manager

TEST_DATA_PATH = 'test/data/filetype'

test_file = os.listdir(TEST_DATA_PATH )

print("支援的檔案格式:", parser_manager.get_supported_formats())

test_file = [os.path.join(TEST_DATA_PATH,file) for file in test_file]


# 單個檔案讀取
result = parser_manager.parse_file(test_file[0])
print(result.to_dict())
results = parser_manager.parse_multiple_files(test_file)

for result in results:
    print("#"*30)
    print(f"\n檔案: {result.file_path}")
    print(f"狀態: {'成功' if result.success else '失敗'}")
    print(f"內容: {result.content}")
