# -*- coding: utf-8 -*-
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import argparse
import sys


class FilingService:
    """檔案整理服務，根據 file_paths.json 的映射來整理檔案"""
    
    def __init__(self, mapping_file: str = ".backup/file_paths.json"):
        """
        初始化檔案整理服務
        
        Args:
            mapping_file: 映射檔案的路徑，預設為 .backup/file_paths.json
        """
        self.mapping_file = mapping_file
        self.mapping_data = None
        self.operations_log = []
        self.error_log = []
        
    def load_mapping(self) -> bool:
        """
        載入檔案映射配置
        
        Returns:
            bool: 是否成功載入
        """
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                self.mapping_data = json.load(f)
            print(f"成功載入映射檔案: {self.mapping_file}")
            return True
        except FileNotFoundError:
            print(f"錯誤: 找不到映射檔案 {self.mapping_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"錯誤: 無法解析 JSON 檔案 - {e}")
            return False
        except Exception as e:
            print(f"錯誤: 載入檔案時發生錯誤 - {e}")
            return False
    
    def create_folder_structure(self, base_path: str, dry_run: bool = False) -> List[str]:
        """
        建立所需的資料夾結構
        
        Args:
            base_path: 基礎路徑
            dry_run: 是否為預覽模式
            
        Returns:
            List[str]: 建立的資料夾列表
        """
        created_folders = []
        
        if not self.mapping_data:
            print("錯誤: 尚未載入映射資料")
            return created_folders
            
        # 從 file_paths 中提取所有需要的資料夾
        required_folders = set()
        for file_mapping in self.mapping_data.get("file_paths", []):
            new_path = Path(file_mapping["new"])
            folder_path = new_path.parent
            required_folders.add(str(folder_path))
        
        # 建立資料夾
        for folder in sorted(required_folders):
            folder_path = Path(folder)
            if not folder_path.exists():
                if not dry_run:
                    try:
                        folder_path.mkdir(parents=True, exist_ok=True)
                        created_folders.append(str(folder_path))
                        print(f"建立資料夾: {folder_path}")
                    except Exception as e:
                        error_msg = f"無法建立資料夾 {folder_path}: {e}"
                        print(f"錯誤: {error_msg}")
                        self.error_log.append(error_msg)
                else:
                    print(f"[預覽] 將建立資料夾: {folder_path}")
                    created_folders.append(str(folder_path))
                    
        return created_folders
    
    def organize_files(self, mode: str = "copy", dry_run: bool = False, 
                      backup: bool = False) -> Tuple[int, int]:
        """
        執行檔案整理
        
        Args:
            mode: 操作模式 ("copy" 或 "move")
            dry_run: 是否為預覽模式
            backup: 是否備份原始檔案（僅在 move 模式下有效）
            
        Returns:
            Tuple[int, int]: (成功數量, 失敗數量)
        """
        if not self.mapping_data:
            print("錯誤: 尚未載入映射資料")
            return 0, 0
            
        success_count = 0
        fail_count = 0
        
        # 先建立資料夾結構
        self.create_folder_structure(".", dry_run)
        
        # 處理每個檔案
        file_mappings = self.mapping_data.get("file_paths", [])
        total_files = len(file_mappings)
        
        print(f"\n開始整理 {total_files} 個檔案 (模式: {mode})...")
        
        for idx, file_mapping in enumerate(file_mappings, 1):
            original_path = Path(file_mapping["original"])
            new_path = Path(file_mapping["new"])
            
            # 進度顯示
            print(f"\n[{idx}/{total_files}] 處理檔案: {original_path.name}")
            
            # 檢查原始檔案是否存在
            if not original_path.exists():
                error_msg = f"原始檔案不存在: {original_path}"
                print(f"  錯誤: {error_msg}")
                self.error_log.append(error_msg)
                fail_count += 1
                continue
            
            # 執行操作
            if dry_run:
                print(f"  [預覽] {mode}: {original_path} -> {new_path}")
                success_count += 1
            else:
                success = self._process_file(original_path, new_path, mode, backup)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    
        # 顯示結果摘要
        print(f"\n整理完成!")
        print(f"成功: {success_count} 個檔案")
        print(f"失敗: {fail_count} 個檔案")
        
        return success_count, fail_count
    
    def _process_file(self, original_path: Path, new_path: Path, 
                     mode: str, backup: bool) -> bool:
        """
        處理單一檔案
        
        Args:
            original_path: 原始檔案路徑
            new_path: 新檔案路徑
            mode: 操作模式 ("copy" 或 "move")
            backup: 是否備份
            
        Returns:
            bool: 是否成功
        """
        try:
            # 如果目標檔案已存在，詢問是否覆蓋
            if new_path.exists():
                print(f"  警告: 目標檔案已存在: {new_path}")
                # 這裡可以加入詢問使用者的邏輯
                
            # 建立備份（如果需要）
            if backup and mode == "move":
                backup_path = Path(".backup") / "original_files" / original_path.name
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original_path, backup_path)
                print(f"  已備份至: {backup_path}")
            
            # 執行操作
            if mode == "copy":
                shutil.copy2(original_path, new_path)
                print(f"  已複製: {original_path} -> {new_path}")
            elif mode == "move":
                shutil.move(str(original_path), str(new_path))
                print(f"  已移動: {original_path} -> {new_path}")
            else:
                raise ValueError(f"不支援的模式: {mode}")
                
            # 記錄操作
            self.operations_log.append({
                "action": mode,
                "original": str(original_path),
                "new": str(new_path),
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            error_msg = f"處理檔案時發生錯誤 {original_path}: {e}"
            print(f"  錯誤: {error_msg}")
            self.error_log.append(error_msg)
            return False
    
    def save_operation_log(self, log_file: str = ".backup/filing_log.json"):
        """
        儲存操作日誌
        
        Args:
            log_file: 日誌檔案路徑
        """
        log_data = {
            "execution_time": datetime.now().isoformat(),
            "mapping_file": self.mapping_file,
            "operations": self.operations_log,
            "errors": self.error_log
        }
        
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            print(f"\n操作日誌已儲存至: {log_file}")
        except Exception as e:
            print(f"儲存日誌時發生錯誤: {e}")
    
    def rollback(self, log_file: str = ".backup/filing_log.json"):
        """
        根據日誌回滾操作
        
        Args:
            log_file: 日誌檔案路徑
        """
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                
            operations = log_data.get("operations", [])
            if not operations:
                print("沒有可回滾的操作")
                return
                
            print(f"開始回滾 {len(operations)} 個操作...")
            
            # 反向執行操作
            for op in reversed(operations):
                if op["action"] == "move":
                    # 將檔案移回原位
                    try:
                        shutil.move(op["new"], op["original"])
                        print(f"已回滾: {op['new']} -> {op['original']}")
                    except Exception as e:
                        print(f"回滾失敗: {e}")
                elif op["action"] == "copy":
                    # 刪除複製的檔案
                    try:
                        os.remove(op["new"])
                        print(f"已刪除複製的檔案: {op['new']}")
                    except Exception as e:
                        print(f"刪除失敗: {e}")
                        
        except FileNotFoundError:
            print(f"找不到日誌檔案: {log_file}")
        except Exception as e:
            print(f"回滾時發生錯誤: {e}")
    
    def cleanup_empty_folders(self, target_path: str = "test/data/textIO"):
        """
        清理空的資料夾
        
        Args:
            target_path: 目標路徑
        """
        print(f"\n清理空資料夾: {target_path}")
        removed_count = 0
        
        for root, dirs, files in os.walk(target_path, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    # 如果資料夾是空的，則刪除
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        print(f"已刪除空資料夾: {dir_path}")
                        removed_count += 1
                except Exception as e:
                    print(f"無法刪除資料夾 {dir_path}: {e}")
        
        print(f"共清理 {removed_count} 個空資料夾")


def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description="檔案整理服務 - 根據 AI 分類結果整理檔案",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python filing_service.py                    # 預設複製模式
  python filing_service.py --mode move        # 移動檔案
  python filing_service.py --dry-run          # 預覽模式
  python filing_service.py --mode move --backup  # 移動並備份
  python filing_service.py --rollback         # 回滾操作
        """
    )
    
    parser.add_argument(
        "--mapping", 
        default=".backup/file_paths.json",
        help="映射檔案路徑 (預設: .backup/file_paths.json)"
    )
    
    parser.add_argument(
        "--mode", 
        choices=["copy", "move"],
        default="copy",
        help="操作模式 (預設: copy)"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="預覽模式，不實際執行操作"
    )
    
    parser.add_argument(
        "--backup", 
        action="store_true",
        help="在移動模式下備份原始檔案"
    )
    
    parser.add_argument(
        "--rollback", 
        action="store_true",
        help="根據日誌回滾上次操作"
    )
    
    parser.add_argument(
        "--cleanup", 
        action="store_true",
        help="清理空資料夾"
    )
    
    args = parser.parse_args()
    
    # 建立服務實例
    service = FilingService(args.mapping)
    
    # 執行清理
    if args.cleanup:
        service.cleanup_empty_folders()
        return
    
    # 執行回滾
    if args.rollback:
        service.rollback()
        return
    
    # 載入映射
    if not service.load_mapping():
        sys.exit(1)
    
    # 執行整理
    success, fail = service.organize_files(
        mode=args.mode,
        dry_run=args.dry_run,
        backup=args.backup
    )
    
    # 儲存日誌（非預覽模式）
    if not args.dry_run and (success > 0 or fail > 0):
        service.save_operation_log()


if __name__ == "__main__":
    # 如果直接執行此檔案，執行測試套件
    import time
    
    print("=" * 60)
    print("檔案整理服務測試套件")
    print("=" * 60)
    
    # 測試 1: 預覽模式
    print("\n[測試 1] 預覽模式測試")
    print("-" * 40)
    service = FilingService()
    if service.load_mapping():
        service.organize_files(mode="copy", dry_run=True)
    
    time.sleep(1)
    
    # 測試 2: 實際複製檔案
    print("\n\n[測試 2] 複製檔案測試")
    print("-" * 40)
    confirm = input("是否執行實際複製？(y/n): ")
    if confirm.lower() == 'y':
        service = FilingService()
        if service.load_mapping():
            success, fail = service.organize_files(mode="copy", dry_run=False)
            if success > 0:
                service.save_operation_log()
    
    time.sleep(1)
    
    # 測試 3: 檢查結果
    print("\n\n[測試 3] 檢查檔案結構")
    print("-" * 40)
    test_path = Path("test/data/textIO")
    if test_path.exists():
        # 顯示建立的資料夾
        folders = [f for f in test_path.iterdir() if f.is_dir()]
        print(f"找到 {len(folders)} 個資料夾:")
        for folder in sorted(folders):
            files = list(folder.glob("*"))
            print(f"  {folder.name}/ ({len(files)} 個檔案)")
            for file in files[:3]:  # 最多顯示3個檔案
                print(f"    - {file.name}")
            if len(files) > 3:
                print(f"    ... 還有 {len(files) - 3} 個檔案")
    
    time.sleep(1)
    
    # 測試 4: 回滾測試
    print("\n\n[測試 4] 回滾功能測試")
    print("-" * 40)
    log_file = Path(".backup/filing_log.json")
    if log_file.exists():
        confirm = input("是否執行回滾操作？(y/n): ")
        if confirm.lower() == 'y':
            service = FilingService()
            service.rollback()
            
            # 清理空資料夾
            print("\n清理空資料夾...")
            service.cleanup_empty_folders()
    else:
        print("沒有找到操作日誌，無法執行回滾")
    
    # 測試 5: 移動模式測試
    print("\n\n[測試 5] 移動模式測試（含備份）")
    print("-" * 40)
    print("注意: 此測試會移動檔案，請確保已備份重要資料")
    confirm = input("是否執行移動測試？(y/n): ")
    if confirm.lower() == 'y':
        # 先建立測試檔案
        test_file = Path("test/data/textIO/test_move.txt")
        test_file.write_text("這是測試移動功能的檔案", encoding='utf-8')
        
        # 建立測試映射
        test_mapping = {
            "file_paths": [{
                "original": str(test_file),
                "new": "test/data/textIO/TestFolder/test_move.txt"
            }],
            "folder_mappings": {
                "TestFolder": ["test_move.txt"]
            }
        }
        
        # 儲存測試映射
        test_mapping_file = ".backup/test_mapping.json"
        with open(test_mapping_file, 'w', encoding='utf-8') as f:
            json.dump(test_mapping, f, ensure_ascii=False, indent=2)
        
        # 執行移動
        service = FilingService(test_mapping_file)
        if service.load_mapping():
            service.organize_files(mode="move", dry_run=False, backup=True)
            service.save_operation_log(".backup/test_filing_log.json")
        
        # 檢查結果
        if Path("test/data/textIO/TestFolder/test_move.txt").exists():
            print("✓ 檔案移動成功")
        if Path(".backup/original_files/test_move.txt").exists():
            print("✓ 備份檔案成功")
    
    print("\n\n測試完成！")
    print("=" * 60)