#!/usr/bin/env python3
"""
File Organizer CLI Tool
A command-line interface for organizing files based on their content using AI classification.
"""

import argparse
import os
import sys
import json
import datetime
import shutil
from typing import Dict, List

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class FileOrganizerCLI:
    """Enhanced CLI wrapper for the file organization service"""
    
    def __init__(self):
        self._organizer = None
    
    @property
    def organizer(self):
        """Lazy load the Organizer to avoid loading models on --help"""
        if self._organizer is None:
            from lib.service.organize_service import Organizer
            self._organizer = Organizer()
        return self._organizer
        
    def preview_organization(self, target_path: str) -> Dict:
        """
        Preview the organization without actually moving files
        
        Args:
            target_path: Directory to organize
            
        Returns:
            Dict containing preview information
        """
        # Lazy imports to avoid loading models
        from lib.file_scanner import FileScanner
        from lib.file_parser import parser_manager
        from lib.folder_namer.folder_namer import create_name
        from tqdm import tqdm
        
        print("\n🔍 Starting preview mode...")
        
        # Step 1: Scan files
        print("\n📂 Scanning files...")
        scanner = FileScanner(target_path=target_path)
        scanner_result = scanner.scan_with_details(save_result=False)
        file_paths = [file_path.get("path", None) for file_path in scanner_result.get("original_files", [])]
        
        if not file_paths:
            print("❌ No files found to organize!")
            return {}
        
        print(f"✓ Found {len(file_paths)} files")
        
        # Step 2: Parse files
        print("\n📄 Analyzing file contents...")
        parsed_results = []
        with tqdm(total=len(file_paths), desc="Parsing files", unit="file") as pbar:
            for file_path in file_paths:
                try:
                    result = parser_manager.parse_single_file(file_path)
                    parsed_results.append(result)
                except Exception as e:
                    print(f"\n⚠️  Error parsing {os.path.basename(file_path)}: {str(e)}")
                    parsed_results.append(None)
                pbar.update(1)
        
        # Prepare summaries
        now = datetime.datetime.now()
        parser_results = {
            "scan_time": now.isoformat(),
            "summaries": []
        }
        
        for file_path, result in zip(file_paths, parsed_results):
            if result:
                parser_results["summaries"].append({
                    "summary": result.content,
                    "path": file_path,
                    "name": os.path.basename(file_path)
                })
        
        # Step 3: Generate folder structure
        print("\n🏷️  Classifying files...")
        file_paths_dict = create_name.process_files(
            summaries_data=parser_results,
            base_output_dir=target_path
        )
        
        # Convert to preview format
        preview_data = {
            "total_files": len(file_paths),
            "parsed_files": len(parser_results["summaries"]),
            "folder_mappings": {},
            "file_movements": []
        }
        
        # Group files by folder
        for file_info in file_paths_dict.get("file_paths", []):
            original_path = file_info["original"]
            new_path = file_info["new"]
            relative_new = os.path.relpath(new_path, target_path)
            folder_name = os.path.dirname(relative_new)
            
            if folder_name not in preview_data["folder_mappings"]:
                preview_data["folder_mappings"][folder_name] = []
            
            preview_data["folder_mappings"][folder_name].append(os.path.basename(original_path))
            preview_data["file_movements"].append({
                "from": original_path,
                "to": new_path
            })
        
        return preview_data
    
    def list_backups(self, target_path: str) -> List[Dict]:
        """List available backups in the target directory"""
        backup_dir = os.path.join(target_path, ".backup")
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        backup_file = os.path.join(backup_dir, "file_paths.json")
        if os.path.exists(backup_file):
            # Get modification time of the backup
            mtime = os.path.getmtime(backup_file)
            backup_time = datetime.datetime.fromtimestamp(mtime)
            
            # Read backup data to get more info
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_count = len(data.get("file_paths", []))
                    folder_count = len(data.get("folder_mappings", {}))
            except:
                file_count = 0
                folder_count = 0
            
            backups.append({
                "time": backup_time,
                "file_count": file_count,
                "folder_count": folder_count,
                "path": backup_dir
            })
        
        return backups
    
    def display_preview(self, preview_data: Dict):
        """Display preview results in a user-friendly format"""
        print("\n" + "="*60)
        print("📊 PREVIEW RESULTS")
        print("="*60)
        
        print(f"\n📈 Summary:")
        print(f"  • Total files found: {preview_data['total_files']}")
        print(f"  • Files analyzed: {preview_data['parsed_files']}")
        print(f"  • Folders to create: {len(preview_data['folder_mappings'])}")
        
        print(f"\n📁 Proposed folder structure:")
        for folder, files in sorted(preview_data['folder_mappings'].items()):
            print(f"\n  📂 {folder}/")
            for file in sorted(files)[:5]:  # Show first 5 files
                print(f"     • {file}")
            if len(files) > 5:
                print(f"     ... and {len(files) - 5} more files")
        
        print("\n" + "="*60)
        print("ℹ️  This is a preview. No files have been moved.")
        print("💡 Run without --preview to actually organize the files.")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Organize files based on their content using AI classification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - organize files by topic
  python file_organizer.py --path /target/folder --strategy topic
  
  # Preview mode - see what would happen without moving files
  python file_organizer.py --path /target/folder --preview
  
  # Restore files to original locations
  python file_organizer.py --path /target/folder --restore
  
  # List available backups
  python file_organizer.py --path /target/folder --list-backups
        """
    )
    
    parser.add_argument(
        '--path',
        type=str,
        required=True,
        help='Path to the directory to organize'
    )
    
    parser.add_argument(
        '--strategy',
        type=str,
        choices=['topic'],
        default='topic',
        help='Organization strategy (currently only "topic" is supported)'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview the organization without moving files'
    )
    
    parser.add_argument(
        '--restore',
        action='store_true',
        help='Restore files to their original locations using backup'
    )
    
    parser.add_argument(
        '--list-backups',
        action='store_true',
        help='List available backups for the target directory'
    )
    
    args = parser.parse_args()
    
    # Validate path
    if not os.path.exists(args.path):
        print(f"❌ Error: Path '{args.path}' does not exist")
        sys.exit(1)
    
    if not os.path.isdir(args.path):
        print(f"❌ Error: Path '{args.path}' is not a directory")
        sys.exit(1)
    
    # Check write permissions
    if not os.access(args.path, os.W_OK):
        print(f"❌ Error: No write permission for directory '{args.path}'")
        sys.exit(1)
    
    cli = FileOrganizerCLI()
    
    try:
        # List backups mode
        if args.list_backups:
            backups = cli.list_backups(args.path)
            if backups:
                print("\n📦 Available backups:")
                for backup in backups:
                    time_str = backup['time'].strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n  📅 Backup Time: {time_str}")
                    print(f"  📁 Location: {backup['path']}")
                    print(f"  📊 Contains: {backup['file_count']} files organized into {backup['folder_count']} folders")
                print("\n💡 Use --restore to restore files to their original locations")
            else:
                print("\n❌ No backups found in this directory")
                print("💡 Backups are created when you organize files without --preview")
            sys.exit(0)
        
        # Restore mode
        if args.restore:
            print(f"\n🔄 Starting restore operation for: {args.path}")
            from lib.restore.restore_folder import restore_folder
            restore_folder(args.path)
            sys.exit(0)
        
        # Preview mode
        if args.preview:
            preview_data = cli.preview_organization(args.path)
            if preview_data:
                cli.display_preview(preview_data)
            sys.exit(0)
        
        # Normal organization mode
        print(f"\n🚀 Starting file organization for: {args.path}")
        print(f"📋 Strategy: {args.strategy}")
        print("\n" + "="*60)
        
        # Create backup directory
        os.makedirs(os.path.join(args.path, ".backup"), exist_ok=True)
        
        # Start organization with progress tracking
        start_time = datetime.datetime.now()
        
        # Use the original organizer
        cli.organizer.start_organize(args.path)
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*60)
        print("✅ Organization completed successfully!")
        print(f"⏱️  Total time: {duration:.2f} seconds")
        print(f"💾 Backup saved in: {args.path}/.backup/")
        print("ℹ️  Use --restore to undo the organization")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during organization: {str(e)}")
        print("💡 Tip: Check file permissions and available disk space")
        sys.exit(1)


if __name__ == "__main__":
    main()