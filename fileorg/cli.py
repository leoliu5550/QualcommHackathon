"""
FileOrg 命令行介面
提供檔案整理工具的命令行入口點
"""
import sys
import os
import json
import argparse
import shutil

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='智慧檔案整理工具 - 使用 AI 技術自動分類與整理檔案'
    )
    parser.add_argument('target_path', help='要整理的目標目錄')
    parser.add_argument('--preview', action='store_true', 
                       help='預覽模式 - 不移動檔案，只顯示整理計畫')
    parser.add_argument('--restore', action='store_true',
                       help='還原模式 - 將檔案還原到原始位置')
    
    args = parser.parse_args()
    
    # 驗證參數組合
    if args.preview and args.restore:
        parser.error("--preview 和 --restore 不能同時使用")
    
    return args

def check_existing_backup(target_path):
    """檢查是否存在備份檔案"""
    backup_file = os.path.join(target_path, ".backup", "file_paths.json")
    return os.path.exists(backup_file)

def load_backup_data(target_path):
    """載入備份資料"""
    backup_file = os.path.join(target_path, ".backup", "file_paths.json")
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"載入備份資料時發生錯誤: {e}")
        return None

def apply_backup_structure(backup_data):
    """套用備份的資料夾結構"""
    file_paths = backup_data.get("file_paths", [])
    moved_count = 0
    
    for file_info in file_paths:
        original_path = os.path.normpath(file_info["original"])
        new_path = os.path.normpath(file_info["new"])
        
        # 檢查檔案是否存在於原始位置
        if os.path.exists(original_path):
            # 建立目標目錄（如果不存在）
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            try:
                shutil.move(original_path, new_path)
                print(f"已移動: {original_path} -> {new_path}")
                moved_count += 1
            except Exception as e:
                print(f"移動失敗 {original_path} 到 {new_path}: {e}")
        else:
            print(f"警告: 找不到原始檔案: {original_path}")
    
    print(f"\n已根據備份結構移動 {moved_count}/{len(file_paths)} 個檔案")

def run_preview_mode(target_path):
    """執行預覽模式（不移動檔案）"""
    print("執行預覽模式 - 不會移動任何檔案")
    print("-" * 50)
    
    # 延遲載入，只在需要時載入
    from fileorg.core.organizer import Organizer
    
    # 建立備份目錄
    os.makedirs(os.path.join(target_path, ".backup"), exist_ok=True)
    
    # 初始化整理器
    organizer = Organizer()
    organizer.target_path = target_path
    
    # 步驟 1: 掃描檔案
    print("掃描檔案中...")
    scanner_result = organizer._file_scanner()
    print(f"找到 {len(scanner_result)} 個檔案")
    
    # 步驟 2: 解析檔案
    print("\n解析檔案內容中...")
    file_parsed = organizer._file_parser(scanner_result=scanner_result, save_result=True)
    
    # 步驟 3: 生成資料夾結構（但不移動檔案）
    print("\n生成資料夾結構中...")
    generate_result = organizer._generate_folder(file_parsed, base_output_dir=target_path, save_result=True, generate_report=True)
    
    # 顯示預覽結果
    print("\n" + "="*60)
    print("預覽結果:")
    print("="*60)
    
    print(f"\n備份 JSON 已建立於: {os.path.join(target_path, '.backup', 'file_paths.json')}")
    print(f"分類時間: {generate_result.get('classification_time', 'N/A')}")
    
    print("\n建議的資料夾結構:")
    for folder, files in generate_result.get("folder_mappings", {}).items():
        print(f"\n{folder}:")
        for file in files:
            print(f"  - {file}")
    
    print("\n" + "-"*60)
    print("若要套用此整理方案，請執行時不加 --preview 參數")
    
    return generate_result

def run_standard_mode(target_path):
    """執行完整的整理流程"""
    # 先檢查是否有備份檔案存在
    if check_existing_backup(target_path):
        print("找到現有的備份檔案")
        backup_data = load_backup_data(target_path)
        
        if backup_data:
            print("套用已儲存的資料夾結構...")
            apply_backup_structure(backup_data)
            return
        else:
            print("備份檔案損壞或空白，執行完整整理流程...")
    
    # 只在真正需要時才載入 Organizer
    from fileorg.core.organizer import Organizer
    
    # 執行完整的整理流程
    print("執行完整整理流程...")
    
    # 建立備份目錄
    os.makedirs(os.path.join(target_path, ".backup"), exist_ok=True)
    
    # 執行整理
    organizer = Organizer()
    organizer.start_organize(target_path)
    
    print("\n檔案整理完成！")

def main():
    # 解析命令行參數
    args = parse_arguments()
    
    # 正規化路徑處理 - 支援 Windows/Linux/macOS
    target_path = os.path.normpath(os.path.abspath(args.target_path))
    
    # 驗證目標路徑
    if not os.path.exists(target_path):
        print(f"錯誤: 路徑 '{target_path}' 不存在")
        sys.exit(1)
    
    try:
        if args.restore:
            # 還原模式 - 延遲載入
            from fileorg.restore.restore_folder import restore_folder
            restore_folder(target_path)
        elif args.preview:
            # 預覽模式
            run_preview_mode(target_path)
        else:
            # 標準模式
            run_standard_mode(target_path)
    except Exception as e:
        print(f"執行過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    """
    使用範例:
    - 預覽模式: fileorg test/data/textIO --preview
    - 標準模式: fileorg test/data/textIO
    - 還原模式: fileorg test/data/textIO --restore
    """
    main()