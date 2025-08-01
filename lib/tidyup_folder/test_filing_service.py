# -*- coding: utf-8 -*-
"""
檔案整理服務測試腳本
自動化測試所有功能
"""
import os
import sys
import time
import json
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib.task4.filing_service import FilingService


def print_section(title):
    """打印測試區段標題"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def test_preview_mode():
    """測試 1: 預覽模式"""
    print_section("測試 1: 預覽模式")
    
    service = FilingService()
    if service.load_mapping():
        service.organize_files(mode="copy", dry_run=True)
        print("\n[OK] 預覽模式測試完成")
    else:
        print("\n[FAIL] 無法載入映射檔案")
    
    time.sleep(1)


def test_copy_files():
    """測試 2: 複製檔案"""
    print_section("測試 2: 複製檔案功能")
    
    service = FilingService()
    if service.load_mapping():
        print("\n執行實際複製...")
        success, fail = service.organize_files(mode="copy", dry_run=False)
        
        if success > 0:
            service.save_operation_log()
            print(f"\n[OK] 複製測試完成: 成功 {success} 個, 失敗 {fail} 個")
        else:
            print(f"\n[FAIL] 複製失敗")
    
    time.sleep(1)


def test_check_structure():
    """測試 3: 檢查檔案結構"""
    print_section("測試 3: 檢查檔案結構")
    
    test_path = Path("test/data/textIO")
    if test_path.exists():
        # 顯示建立的資料夾
        folders = [f for f in test_path.iterdir() if f.is_dir()]
        print(f"\n找到 {len(folders)} 個資料夾:")
        
        for folder in sorted(folders):
            files = list(folder.glob("*"))
            print(f"\n  [{folder.name}] ({len(files)} 個檔案)")
            
            # 顯示前3個檔案
            for i, file in enumerate(files[:3]):
                print(f"    - {file.name}")
            
            if len(files) > 3:
                print(f"    - ... 還有 {len(files) - 3} 個檔案")
        
        print("\n[OK] 檔案結構檢查完成")
    else:
        print("\n[FAIL] 找不到測試路徑")
    
    time.sleep(1)


def test_rollback():
    """測試 4: 回滾功能"""
    print_section("測試 4: 回滾功能")
    
    log_file = Path(".backup/filing_log.json")
    if log_file.exists():
        print("\n執行回滾操作...")
        service = FilingService()
        service.rollback()
        
        # 清理空資料夾
        print("\n清理空資料夾...")
        service.cleanup_empty_folders()
        
        print("\n[OK] 回滾測試完成")
    else:
        print("\n[FAIL] 沒有找到操作日誌，無法執行回滾")
    
    time.sleep(1)


def test_move_with_backup():
    """測試 5: 移動模式（含備份）"""
    print_section("測試 5: 移動模式測試（含備份）")
    
    # 建立測試檔案
    test_file = Path("test/data/textIO/test_move.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("這是測試移動功能的檔案\n測試時間: " + str(time.time()), encoding='utf-8')
    print(f"\n建立測試檔案: {test_file}")
    
    # 建立測試映射
    test_mapping = {
        "file_paths": [{
            "original": str(test_file),
            "new": "test/data/textIO/TestFolder/test_move.txt"
        }],
        "folder_mappings": {
            "TestFolder": ["test_move.txt"]
        },
        "classification_time": datetime.now().isoformat()
    }
    
    # 儲存測試映射
    test_mapping_file = ".backup/test_mapping.json"
    os.makedirs(".backup", exist_ok=True)
    with open(test_mapping_file, 'w', encoding='utf-8') as f:
        json.dump(test_mapping, f, ensure_ascii=False, indent=2)
    print(f"建立測試映射: {test_mapping_file}")
    
    # 執行移動
    print("\n執行移動操作（含備份）...")
    service = FilingService(test_mapping_file)
    if service.load_mapping():
        success, fail = service.organize_files(mode="move", dry_run=False, backup=True)
        service.save_operation_log(".backup/test_filing_log.json")
        
        # 檢查結果
        moved_file = Path("test/data/textIO/TestFolder/test_move.txt")
        backup_file = Path(".backup/original_files/test_move.txt")
        
        if moved_file.exists():
            print("[OK] 檔案移動成功")
        else:
            print("[FAIL] 檔案移動失敗")
            
        if backup_file.exists():
            print("[OK] 備份檔案成功")
        else:
            print("[FAIL] 備份檔案失敗")
    
    # 清理測試檔案
    print("\n清理測試檔案...")
    for path in [moved_file, backup_file, test_file]:
        if path.exists():
            path.unlink()
            print(f"  刪除: {path}")
    
    # 清理測試資料夾
    test_folder = Path("test/data/textIO/TestFolder")
    if test_folder.exists() and not list(test_folder.iterdir()):
        test_folder.rmdir()
        print(f"  刪除空資料夾: {test_folder}")
    
    print("\n[OK] 移動測試完成")


def test_help_command():
    """測試 6: 說明指令"""
    print_section("測試 6: 說明指令")
    
    print("\n執行: python filing_service.py --help")
    os.system("python lib/task4/filing_service.py --help")
    
    print("\n[OK] 說明指令測試完成")


def main():
    """主測試程式"""
    print("=" * 60)
    print(" " * 18 + "檔案整理服務完整測試套件" + " " * 18)
    print("=" * 60)
    
    # 測試清單
    tests = [
        ("預覽模式", test_preview_mode),
        ("複製檔案", test_copy_files),
        ("檢查結構", test_check_structure),
        ("回滾功能", test_rollback),
        ("移動模式", test_move_with_backup),
        ("說明指令", test_help_command),
    ]
    
    # 顯示測試計畫
    print("\n測試計畫:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"  {i}. {name}")
    
    print("\n開始執行測試...\n")
    
    # 執行所有測試
    for i, (name, test_func) in enumerate(tests, 1):
        try:
            test_func()
        except Exception as e:
            print(f"\n[ERROR] 測試 {i} ({name}) 發生錯誤: {e}")
    
    # 測試總結
    print_section("測試總結")
    print("\n所有測試已完成！")
    print("\n重要提示:")
    print("- 複製模式: 保留原始檔案，在新位置建立副本")
    print("- 移動模式: 將檔案移至新位置（可選擇備份）")
    print("- 回滾功能: 可撤銷上次的操作")
    print("- 預覽模式: 查看將執行的操作而不實際執行")


if __name__ == "__main__":
    from datetime import datetime
    main()