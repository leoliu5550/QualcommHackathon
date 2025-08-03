import json
import os
import shutil
from typing import Dict

class FileRestorer:
    """Restores files from sorted location back to their original paths"""
    
    def __init__(self, target_path: str):
        self.target_path = target_path
        self.backup_file = os.path.join(target_path, ".backup", "file_paths.json")
    
    def restore(self) -> bool:
        """
        Perform the restore operation
        
        Returns:
            bool: Whether the restore was successful
        """
        try:
            backup_data = self._load_backup_data()
            if not backup_data:
                print(f"Error: No backup data found at {self.backup_file}")
                return False
            
            file_paths = backup_data.get("file_paths", [])
            if not file_paths:
                print("Error: No file paths found in backup data")
                return False
            
            restored_count = 0
            for file_info in file_paths:
                if self._restore_single_file(file_info):
                    restored_count += 1
            
            self._cleanup_empty_directories(backup_data)
            
            print(f"Successfully restored {restored_count}/{len(file_paths)} files")
            return restored_count == len(file_paths)
            
        except Exception as e:
            print(f"Error during restore operation: {e}")
            return False
    
    def _load_backup_data(self) -> Dict:
        """Load backup JSON data"""
        try:
            if not os.path.exists(self.backup_file):
                return {}
            
            with open(self.backup_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading backup data: {e}")
            return {}
    
    def _restore_single_file(self, file_info: Dict) -> bool:
        """
        Restore a single file
        
        Args:
            file_info: Dict with 'original' and 'new' paths
            
        Returns:
            bool: Whether the file was successfully restored
        """
        try:
            original_path = file_info.get("original")
            new_path = file_info.get("new")
            
            if not original_path or not new_path:
                print("Error: Missing original or new path in file info")
                return False
            
            new_path = new_path.replace('\\', '/')
            
            if not os.path.isabs(new_path):
                if new_path.startswith('test/data/textIO/'):
                    new_path = new_path[len('test/data/textIO/'):]
                new_path = os.path.join(self.target_path, new_path)
            
            if not os.path.exists(new_path):
                print(f"Warning: File not found at new location: {new_path}")
                return False
            
            original_dir = os.path.dirname(original_path)
            os.makedirs(original_dir, exist_ok=True)
            
            shutil.move(new_path, original_path)
            print(f"Restored: {new_path} -> {original_path}")
            return True
            
        except Exception as e:
            print(f"Failed to restore file {file_info}: {e}")
            return False
    
    def _cleanup_empty_directories(self, backup_data: Dict):
        """Remove empty directories after restore"""
        try:
            folder_mappings = backup_data.get("folder_mappings", {})
            
            for folder_name in folder_mappings.keys():
                folder_path = os.path.join(self.target_path, folder_name)
                
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    try:
                        if not os.listdir(folder_path):
                            os.rmdir(folder_path)
                            print(f"Removed empty directory: {folder_path}")
                    except OSError:
                        pass
                        
        except Exception as e:
            print(f"Error during directory cleanup: {e}")


def restore_folder(target_path: str):
    """
    Entry point for restoring files to their original locations
    
    Args:
        target_path: Target directory
    """
    restorer = FileRestorer(target_path)
    success = restorer.restore()
    
    if success:
        print("File restoration completed successfully!")
    else:
        print("File restoration completed with errors.")
