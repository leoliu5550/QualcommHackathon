"""File restoration module.

Reverts organized files back to their original locations.
Provides safe undo functionality for file organization.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict


class FileRestorer:
    """Restore files to original locations.
    
    Uses backup data to safely undo file organization.
    Cleans up empty directories after restoration.
    """

    def __init__(self, target_path: str):
        """Initialize restorer with target directory.
        
        Args:
            target_path: Root directory containing organized files
        """
        self.target_path = target_path
        self.backup_file = os.path.join(target_path, ".backup", "file_paths.json")

    def restore(self) -> bool:
        """Restore all files to original locations.

        Returns:
            True if all files restored successfully
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
        """Load backup data from JSON file.
        
        Returns:
            Dict with file movement history
        """
        try:
            if not os.path.exists(self.backup_file):
                return {}

            with open(self.backup_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading backup data: {e}")
            return {}

    def _restore_single_file(self, file_info: Dict) -> bool:
        """Restore one file to its original location.

        Args:
            file_info: Dict with 'original' and 'new' paths

        Returns:
            True if file restored successfully
        """
        try:
            original_path = file_info.get("original")
            new_path = file_info.get("new")

            if not original_path or not new_path:
                print("Error: Missing original or new path in file info")
                return False

            # Normalize paths
            original_path = os.path.normpath(original_path)
            new_path = os.path.normpath(new_path)

            # 如果不是絕對路徑，則相對於 target_path
            if not os.path.isabs(new_path):
                # 向下相容：移除舊的硬編碼路徑前綴
                for prefix in ["test/data/textIO/", "test\\data\\textIO\\"]:
                    if new_path.startswith(prefix):
                        new_path = new_path[len(prefix) :]
                        break
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
            # Get or rebuild folder mappings for backward compatibility
            folder_mappings = backup_data.get("folder_mappings", {})
            if not folder_mappings:
                # Rebuild from file_paths if needed
                for file_info in backup_data.get("file_paths", []):
                    if new_path := file_info.get("new"):
                        folder_path = Path(new_path).relative_to(self.target_path).parent
                        if folder_path != Path("."):
                            folder_mappings[str(folder_path).replace("\\", "/")] = []
            
            # Collect all directories to check (including parent directories)
            dirs_to_check = set()
            for folder_name in folder_mappings:
                if folder_name == ".":
                    continue
                path = Path(folder_name)
                # Add this folder and all parent folders
                while path != Path("."):
                    dirs_to_check.add(path)
                    path = path.parent
            
            # Remove empty directories from deepest to shallowest
            for folder_path in sorted(dirs_to_check, key=lambda p: len(p.parts), reverse=True):
                full_path = Path(self.target_path) / folder_path
                try:
                    if full_path.exists() and full_path.is_dir() and not any(full_path.iterdir()):
                        full_path.rmdir()
                        print(f"Removed empty directory: {full_path}")
                except OSError:
                    pass  # Directory not empty or permission issue

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
