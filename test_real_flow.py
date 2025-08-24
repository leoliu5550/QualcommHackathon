#!/usr/bin/env python
"""
快速測試真實檔案流程
用於驗證 textIO 資料夾中的檔案是否能正確處理
"""
import sys
import os
from pathlib import Path

# 將專案加入路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_parsing():
    """測試檔案解析功能"""
    print("=" * 60)
    print("測試檔案解析功能")
    print("=" * 60)
    
    from fileorg.parsers import parser_manager
    
    # 測試資料路徑
    test_dir = Path("tests/fixtures/textIO")
    
    if not test_dir.exists():
        print(f"錯誤: 測試資料夾不存在 {test_dir}")
        return False
    
    # 收集所有檔案
    test_files = [str(f) for f in test_dir.iterdir() if f.is_file()]
    
    print(f"找到 {len(test_files)} 個測試檔案")
    print()
    
    # 解析每個檔案
    success_count = 0
    for file_path in test_files:
        file_name = Path(file_path).name
        result = parser_manager.parse_file(file_path)
        
        if result.success:
            success_count += 1
            print(f"[OK] {file_name}")
            print(f"   類型: {result.file_type}")
            print(f"   內容長度: {len(result.content)} 字元")
            if result.truncated:
                print(f"   註: 內容已截斷 (原始長度: {result.original_length})")
        else:
            print(f"[FAIL] {file_name}")
            print(f"   錯誤: {result.error}")
        print()
    
    print(f"解析成功率: {success_count}/{len(test_files)} ({success_count*100/len(test_files):.1f}%)")
    return success_count == len(test_files)


def test_scanning():
    """測試檔案掃描功能"""
    print("\n" + "=" * 60)
    print("測試檔案掃描功能")
    print("=" * 60)
    
    from fileorg.scanner import FileScanner
    
    test_dir = Path("tests/fixtures/textIO")
    scanner = FileScanner(str(test_dir))
    
    # 執行掃描
    files = scanner.scan_directory()
    print(f"掃描到 {len(files)} 個檔案:")
    
    for file_path in files:
        print(f"  - {Path(file_path).name}")
    
    # 測試詳細掃描
    print("\n執行詳細掃描...")
    result = scanner.scan_with_details(save_result=False)
    
    print(f"掃描時間: {result.get('scan_time', 'N/A')}")
    print(f"目標路徑: {result.get('target_path', 'N/A')}")
    print(f"檔案數量: {len(result.get('original_files', []))}")
    
    return len(files) > 0


def test_classification():
    """測試分類功能（使用 Mock）"""
    print("\n" + "=" * 60)
    print("測試分類功能")
    print("=" * 60)
    
    from unittest.mock import Mock, patch
    from fileorg.classifier.classifier import CreateFolderNamer
    
    # 模擬 LLM
    with patch('fileorg.classifier.classifier.get_llm') as mock_get_llm:
        mock_llm = Mock()
        mock_llm.inference.side_effect = [
            "Documents",
            "Academic", 
            "Spreadsheets",
            "Presentations",
            '[{"foldername": "Documents", "groupname": "Documents"}, {"foldername": "Academic", "groupname": "Academic"}, {"foldername": "Spreadsheets", "groupname": "DataFiles"}, {"foldername": "Presentations", "groupname": "Presentations"}]'
        ]
        mock_get_llm.return_value = mock_llm
        
        namer = CreateFolderNamer()
        
        # 測試資料
        test_summaries = {
            "summaries": [
                {"summary": "Health organizations document", "path": "test1.docx", "name": "test1.docx"},
                {"summary": "Academic paper about statistics", "path": "test2.pdf", "name": "test2.pdf"},
                {"summary": "Excel functions reference", "path": "test3.xlsx", "name": "test3.xlsx"},
                {"summary": "AI presentation slides", "path": "test4.pptx", "name": "test4.pptx"}
            ]
        }
        
        result = namer.process_files(test_summaries, "./output")
        
        print("分類結果:")
        for file_info in result["file_paths"]:
            original = Path(file_info["original"]).name
            new_folder = Path(file_info["new"]).parent.name
            print(f"  {original} → {new_folder}/")
        
        return len(result["file_paths"]) == 4


def test_complete_flow():
    """測試完整流程（不實際移動檔案）"""
    print("\n" + "=" * 60)
    print("測試完整工作流程")
    print("=" * 60)
    
    from unittest.mock import Mock, patch
    from fileorg.core.organizer import Organizer
    import tempfile
    import shutil
    
    # 建立臨時測試目錄
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test"
        
        # 複製測試檔案
        source_dir = Path("tests/fixtures/textIO")
        if source_dir.exists():
            shutil.copytree(source_dir, test_dir)
        else:
            print("錯誤: 測試資料不存在")
            return False
        
        # 模擬 LLM
        with patch('fileorg.classifier.classifier.get_llm') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.inference.return_value = "TestFolder"
            mock_get_llm.return_value = mock_llm
            
            organizer = Organizer()
            organizer.target_path = str(test_dir)
            
            # 執行流程
            print("1. 掃描檔案...")
            scan_result = organizer._file_scanner()
            print(f"   找到 {len(scan_result)} 個檔案")
            
            print("2. 解析檔案內容...")
            parse_result = organizer._file_parser(scan_result, save_result=False)
            print(f"   解析了 {len(parse_result['summaries'])} 個檔案")
            
            print("3. 分類檔案...")
            folder_result = organizer._generate_folder(parse_result, str(test_dir), save_result=False)
            print(f"   生成 {len(folder_result['folder_mappings'])} 個分類資料夾")
            
            print("\n分類結果:")
            for folder, files in folder_result["folder_mappings"].items():
                print(f"  [{folder}]/")
                for file_name in files[:3]:  # 只顯示前3個
                    print(f"     - {file_name}")
                if len(files) > 3:
                    print(f"     ... 還有 {len(files)-3} 個檔案")
            
            return True


def main():
    """主測試函數"""
    print("\n開始測試真實檔案流程\n")
    
    tests = [
        ("檔案解析", test_parsing),
        ("檔案掃描", test_scanning),
        ("檔案分類", test_classification),
        ("完整流程", test_complete_flow)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n[FAIL] {name} 測試失敗: {e}")
            results.append((name, False))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    for name, success in results:
        status = "[通過]" if success else "[失敗]"
        print(f"{name}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n所有測試通過！")
    else:
        print("\n部分測試失敗，請檢查")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())