import sys
import os
import json
import argparse
import shutil
from datetime import datetime
from lib.report_generator import ReportGenerator

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='File organization tool with preview and restore capabilities'
    )
    parser.add_argument('target_path', help='Target directory to organize')
    parser.add_argument('--preview', action='store_true', 
                       help='Preview organization without moving files')
    parser.add_argument('--restore', action='store_true',
                       help='Restore files to original locations')
    
    args = parser.parse_args()
    
    # Validate that preview and restore are not used together
    if args.preview and args.restore:
        parser.error("--preview and --restore cannot be used together")
    
    return args

def check_existing_backup(target_path):
    """Check if backup file exists"""
    backup_file = os.path.join(target_path, ".backup", "file_paths.json")
    return os.path.exists(backup_file)

def load_backup_data(target_path):
    """Load existing backup data"""
    backup_file = os.path.join(target_path, ".backup", "file_paths.json")
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading backup data: {e}")
        return None

def apply_backup_structure(target_path, backup_data):
    """Apply the folder structure from backup JSON"""
    file_paths = backup_data.get("file_paths", [])
    moved_count = 0
    
    for file_info in file_paths:
        original_path = file_info["original"]
        new_path = file_info["new"]
        
        # Check if file exists at original location
        if os.path.exists(original_path):
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            try:
                shutil.move(original_path, new_path)
                print(f"Moved: {original_path} -> {new_path}")
                moved_count += 1
            except Exception as e:
                print(f"Failed to move {original_path} to {new_path}: {e}")
        else:
            print(f"Warning: File not found at original location: {original_path}")
    
    print(f"\nMoved {moved_count}/{len(file_paths)} files based on backup structure")
    
    # 生成報告
    try:
        report_generator = ReportGenerator(target_path)
        report_files = report_generator.generate_reports()
        print("\n已生成報告:")
        print(f"  報告儲存於: {report_files['report_folder']}")
    except Exception as e:
        print(f"生成報告時發生錯誤: {e}")

def run_preview_mode(target_path):
    """Run organization in preview mode (no file movement)"""
    print("Running in PREVIEW mode - no files will be moved")
    print("-" * 50)
    
    # Lazy import - only when needed
    from lib.service.organize_service import Organizer
    
    # Create backup directory
    os.makedirs(os.path.join(target_path, ".backup"), exist_ok=True)
    
    # Initialize organizer
    organizer = Organizer()
    organizer.target_path = target_path
    
    # Step 1: Scan files
    print("Scanning files...")
    scanner_result = organizer._file_scanner()
    print(f"Found {len(scanner_result)} files")
    
    # Step 2: Parse files
    print("\nParsing file contents...")
    file_parsed = organizer._file_parser(scanner_result=scanner_result, save_result=True)
    
    # Step 3: Generate folder structure (but don't move files)
    print("\nGenerating folder structure...")
    generate_result = organizer._generate_folder(file_parsed, base_output_dir=target_path, save_result=True, generate_report=True)
    
    # Display preview results
    print("\n" + "="*60)
    print("PREVIEW RESULTS:")
    print("="*60)
    
    print(f"\nBackup JSON created at: {os.path.join(target_path, '.backup', 'file_paths.json')}")
    print(f"Classification time: {generate_result.get('classification_time', 'N/A')}")
    
    print("\nProposed folder structure:")
    for folder, files in generate_result.get("folder_mappings", {}).items():
        print(f"\n{folder}:")
        for file in files:
            print(f"  - {file}")
    
    print("\n" + "-"*60)
    print("To apply this organization, run without --preview flag")
    
    # Return the backup data
    return generate_result

def run_standard_mode(target_path):
    """Run full organization workflow"""
    # Check if backup exists FIRST - before any imports
    if check_existing_backup(target_path):
        print("Found existing backup file")
        backup_data = load_backup_data(target_path)
        
        if backup_data:
            print("Applying saved folder structure from backup...")
            apply_backup_structure(target_path, backup_data)
            return
        else:
            print("Backup file is corrupted or empty, running full organization...")
    
    # Only import Organizer when we actually need it
    from lib.service.organize_service import Organizer
    
    # Run full organization workflow
    print("Running full organization workflow...")
    
    # Create backup directory
    os.makedirs(os.path.join(target_path, ".backup"), exist_ok=True)
    
    # Run organization
    organizer = Organizer()
    organizer.start_organize(target_path)
    
    print("\nOrganization completed!")

def main():
    # Parse arguments
    args = parse_arguments()
    
    # Validate target path
    if not os.path.exists(args.target_path):
        print(f"Error: Path '{args.target_path}' does not exist")
        sys.exit(1)
    
    try:
        if args.restore:
            # Restore mode - lazy import
            from lib.restore.restore_folder import restore_folder
            restore_folder(args.target_path)
        elif args.preview:
            # Preview mode
            run_preview_mode(args.target_path)
        else:
            # Standard mode
            run_standard_mode(args.target_path)
    except Exception as e:
        print(f"Error during operation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    """
    測試指令: 
    python main.py test/data/textIO
    python main.py test/data/textIO --restore"""
    main()