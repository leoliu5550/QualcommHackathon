"""
cli.py
FileOrg Command Line Interface

This module provides the main entry point for the FileOrg intelligent file organization system.
We're working towards making file organization as intuitive as possible, learning from each
interaction to better understand how humans naturally categorize information.

The CLI supports three primary modes:
- Preview: Safely explore potential organization without moving files
- Organize: Apply AI-powered categorization to transform chaos into structure
- Restore: Completely undo changes when needed

We believe in giving users full control while leveraging AI to reduce manual effort.
Your feedback helps us continuously improve the categorization algorithms.

Example:
    Basic usage from command line::

        $ fileorg /path/to/messy/folder --preview
        $ fileorg /path/to/messy/folder
        $ fileorg /path/to/organized/folder --restore
        $ fileorg start  # 啟動GUI模式

Note:
    This module handles cross-platform path normalization automatically,
    ensuring consistent behavior across Windows, Linux, and macOS.
"""

import sys
import os
import json
import argparse
import shutil


def parse_arguments():
    """
    Parse command line arguments for the FileOrg application.

    We've designed the CLI to be intuitive while providing powerful options.
    The interface continues to evolve based on user feedback and usage patterns.

    Returns:
        argparse.Namespace: Parsed arguments containing:
            - target_path: Directory to process
            - preview: Boolean flag for preview mode
            - restore: Boolean flag for restore mode

    Raises:
        argparse.ArgumentError: If conflicting options are provided

    Example:
        >>> args = parse_arguments()
        >>> print(args.target_path)
        '/home/user/documents'
    """
    parser = argparse.ArgumentParser(
        description="智慧檔案整理工具 - 使用 AI 技術自動分類與整理檔案"
    )
    
    # 讓 target_path 變為可選參數，以支援 GUI 模式
    parser.add_argument("target_path", nargs='?', help="要整理的目標目錄 (GUI 模式時可省略)")
    parser.add_argument(
        "--preview", action="store_true", help="預覽模式 - 不移動檔案，只顯示整理計畫"
    )
    parser.add_argument("--restore", action="store_true", help="還原模式 - 將檔案還原到原始位置")

    args = parser.parse_args()

    # 檢查 GUI 模式
    if args.target_path == "start":
        return args

    # 驗證參數組合
    if args.preview and args.restore:
        parser.error("--preview 和 --restore 不能同時使用")
        
    # 對於非 GUI 模式，target_path 是必需的
    if not args.target_path and not (len(sys.argv) == 2 and sys.argv[1] == "start"):
        parser.error("必須提供目標路徑或使用 'start' 啟動 GUI 模式")

    return args


def check_existing_backup(target_path):
    """
    Check if backup files exist for potential restoration.

    We maintain comprehensive backups to ensure users can always revert changes.
    This reflects our commitment to non-destructive file organization.

    Args:
        target_path (str): Directory to check for backups

    Returns:
        bool: True if backup exists, False otherwise

    Note:
        Backup files are stored in .backup/file_paths.json within the target directory.
        We're exploring cloud backup options for future releases.
    """
    backup_file = os.path.join(target_path, ".backup", "file_paths.json")

    try:
        return os.path.exists(backup_file)
    except PermissionError:
        # Handle the permission error gracefully
        return False


def load_backup_data(target_path):
    """
    Load backup data for file restoration.

    Our backup format is designed to be human-readable JSON, allowing for
    manual inspection and modification if needed. We believe in transparency
    and user empowerment.

    Args:
        target_path (str): Directory containing backup files

    Returns:
        dict: Backup data including file mappings and metadata,
              or None if loading fails

    Example:
        >>> backup = load_backup_data('/home/user/organized')
        >>> print(backup['file_paths'][0])
        {'original': '/path/to/file.txt', 'new': '/organized/path/file.txt'}
    """
    backup_file = os.path.join(target_path, ".backup", "file_paths.json")
    try:
        with open(backup_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"載入備份資料時發生錯誤: {e}")
        return None


def apply_backup_structure(backup_data):
    """
    Apply saved folder structure from backup data.

    This function enables users to apply a previously generated organization
    structure without re-running the AI analysis. We're working on making
    this process even more efficient in future versions.

    Args:
        backup_data (dict): Backup data containing file mappings

    Returns:
        None

    Side Effects:
        Moves files according to the backup structure
        Prints progress messages to stdout

    Note:
        We perform atomic operations where possible to minimize risk
        of data loss during the organization process.
    """
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
    """
    Execute preview mode to show potential organization without moving files.

    Preview mode represents our philosophy of 'look before you leap'. We want
    users to feel confident about the changes before committing to them.
    The AI analyzes content and suggests organization, but you make the final decision.

    Args:
        target_path (str): Directory to analyze

    Returns:
        dict: Organization results including suggested structure

    Features:
        - Non-destructive analysis
        - Generates backup plan for later execution
        - Provides detailed categorization reasoning
        - Shows statistics about the proposed organization

    Example:
        >>> results = run_preview_mode('/home/user/documents')
        >>> print(f"Suggested {len(results['folder_mappings'])} categories")
    """
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
    generate_result = organizer._generate_folder(
        file_parsed, base_output_dir=target_path, save_result=True, generate_report=True
    )

    # 顯示預覽結果
    print("\n" + "=" * 60)
    print("預覽結果:")
    print("=" * 60)

    print(f"\n備份 JSON 已建立於: {os.path.join(target_path, '.backup', 'file_paths.json')}")
    print(f"分類時間: {generate_result.get('classification_time', 'N/A')}")

    print("\n建議的資料夾結構:")
    for folder, files in generate_result.get("folder_mappings", {}).items():
        print(f"\n{folder}:")
        for file in files:
            print(f"  - {file}")

    print("\n" + "-" * 60)
    print("若要套用此整理方案，請執行時不加 --preview 參數")

    return generate_result


def run_standard_mode(target_path):
    """
    Execute complete file organization workflow.

    This is where our AI truly shines - analyzing content, understanding context,
    and creating meaningful categorizations. We're continuously improving our
    algorithms based on real-world usage patterns.

    Args:
        target_path (str): Directory to organize

    Returns:
        None

    Process:
        1. Check for existing backups (apply if found)
        2. Scan all files in directory
        3. Parse content using appropriate extractors
        4. Apply AI categorization
        5. Move files to organized structure
        6. Generate comprehensive reports

    Note:
        We always create backups before moving files. Your data safety
        is our top priority.
    """
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
    """
    Main entry point for the FileOrg CLI application.

    We've designed this to be the simplest possible interface to powerful
    AI-driven file organization. As we continue to develop FileOrg, we remain
    committed to maintaining this simplicity while adding advanced features.

    The function handles:
        - Cross-platform path normalization
        - Input validation
        - Mode selection (preview/organize/restore)
        - Error handling with helpful messages
        - GUI mode integration

    Exit Codes:
        0: Success
        1: Error (invalid path, execution error, etc.)

    Future Enhancements:
        We're exploring batch processing, scheduling, and cloud integration
        to make FileOrg even more powerful while maintaining its ease of use.
    """
    # 解析命令行參數
    args = parse_arguments()
    
    # 檢查是否為 GUI 模式
    if args.target_path == "start" or (len(sys.argv) == 2 and sys.argv[1] == "start"):
        try:
            # 修正導入路徑
            from fileorg.gui.usercli import start_gui
            start_gui()
            return
        except ImportError as e:
            print(f"錯誤: 無法載入 GUI 模組: {e}")
            print("請確認 GUI 模組已正確安裝在 fileorg.gui.usercli")
            sys.exit(1)

    # 確保非 GUI 模式有 target_path
    if not args.target_path:
        print("錯誤: 必須提供目標路徑")
        sys.exit(1)

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
    - GUI 模式: fileorg start
    - 預覽模式: fileorg test/data/textIO --preview
    - 標準模式: fileorg test/data/textIO
    - 還原模式: fileorg test/data/textIO --restore
    """
    main()