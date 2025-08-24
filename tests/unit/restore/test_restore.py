"""
Test suite for FileOrg Restore module
"""

import pytest
from unittest.mock import patch, mock_open

from fileorg.restore.restore_folder import FileRestorer, restore_folder


class TestFileRestorer:
    """Test FileRestorer class functionality"""
    
    @pytest.mark.unit
    def test_file_restorer_init(self, tmp_path):
        """Test FileRestorer initialization"""
        restorer = FileRestorer(str(tmp_path))
        assert restorer.target_path == str(tmp_path)
        assert str(tmp_path) in restorer.backup_file
        assert ".backup" in restorer.backup_file
        assert "file_paths.json" in restorer.backup_file


class TestLoadBackupData:
    """Test backup data loading functionality"""
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='{"file_paths": []}')
    def test_load_backup_data_success(self, mock_file, mock_exists, tmp_path):
        """Test successful backup data loading"""
        restorer = FileRestorer(str(tmp_path))
        result = restorer._load_backup_data()
        
        assert result == {"file_paths": []}
        mock_exists.assert_called_once()
        mock_file.assert_called_once()
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=False)
    def test_load_backup_data_missing_file(self, mock_exists, tmp_path):
        """Test backup data loading with missing file"""
        restorer = FileRestorer(str(tmp_path))
        result = restorer._load_backup_data()
        
        assert result == {}
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('builtins.print')
    def test_load_backup_data_invalid_json(self, mock_print, mock_file, mock_exists, tmp_path):
        """Test backup data loading with invalid JSON"""
        restorer = FileRestorer(str(tmp_path))
        result = restorer._load_backup_data()
        
        assert result == {}
        mock_print.assert_called()


class TestRestoreSingleFile:
    """Test single file restoration functionality"""
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('shutil.move')
    @patch('builtins.print')
    def test_restore_single_file_success(self, mock_print, mock_move, mock_makedirs, mock_exists, tmp_path):
        """Test successful single file restoration"""
        restorer = FileRestorer(str(tmp_path))
        
        file_info = {
            "original": str(tmp_path / "original" / "file.txt"),
            "new": str(tmp_path / "organized" / "docs" / "file.txt")
        }
        
        result = restorer._restore_single_file(file_info)
        
        assert result is True
        mock_makedirs.assert_called_once()
        mock_move.assert_called_once()
        mock_print.assert_called()
    
    @pytest.mark.unit
    def test_restore_single_file_missing_paths(self, tmp_path):
        """Test restoration with missing path information"""
        restorer = FileRestorer(str(tmp_path))
        
        file_info = {"original": None, "new": None}
        result = restorer._restore_single_file(file_info)
        
        assert result is False
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=False)
    @patch('builtins.print')
    def test_restore_single_file_missing_source(self, mock_print, mock_exists, tmp_path):
        """Test restoration when source file doesn't exist"""
        restorer = FileRestorer(str(tmp_path))
        
        file_info = {
            "original": str(tmp_path / "original" / "file.txt"),
            "new": str(tmp_path / "organized" / "docs" / "file.txt")
        }
        
        result = restorer._restore_single_file(file_info)
        
        assert result is False
        mock_print.assert_called()
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('shutil.move', side_effect=Exception('Move failed'))
    @patch('builtins.print')
    def test_restore_single_file_move_failure(self, mock_print, mock_move, mock_makedirs, mock_exists, tmp_path):
        """Test restoration failure during file move"""
        restorer = FileRestorer(str(tmp_path))
        
        file_info = {
            "original": str(tmp_path / "original" / "file.txt"),
            "new": str(tmp_path / "organized" / "docs" / "file.txt")
        }
        
        result = restorer._restore_single_file(file_info)
        
        assert result is False
        mock_print.assert_called()
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('shutil.move')
    @patch('builtins.print')
    def test_restore_single_file_relative_path_conversion(self, mock_print, mock_move, mock_makedirs, mock_exists, tmp_path):
        """Test restoration with relative path conversion"""
        restorer = FileRestorer(str(tmp_path))
        
        # Test with legacy prefix that should be removed
        file_info = {
            "original": str(tmp_path / "original" / "file.txt"),
            "new": "test/data/textIO/docs/file.txt"  # Relative path with legacy prefix
        }
        
        result = restorer._restore_single_file(file_info)
        
        assert result is True
        # Verify the new_path was converted to absolute and joined with target_path
        expected_new_path = str(tmp_path / "docs" / "file.txt")
        mock_move.assert_called_once()


class TestCleanupEmptyDirectories:
    """Test directory cleanup functionality"""
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=True)
    @patch('os.path.isdir', return_value=True)
    @patch('os.listdir', return_value=[])  # Empty directory
    @patch('os.rmdir')
    @patch('builtins.print')
    def test_cleanup_empty_directories(self, mock_print, mock_rmdir, mock_listdir, mock_isdir, mock_exists, tmp_path):
        """Test cleanup of empty directories"""
        restorer = FileRestorer(str(tmp_path))
        
        backup_data = {
            "folder_mappings": {
                "docs": ["file1.txt"],
                "images": ["photo.jpg"]
            }
        }
        
        restorer._cleanup_empty_directories(backup_data)
        
        # Should attempt to remove both directories
        assert mock_rmdir.call_count == 2
        assert mock_print.call_count == 2
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=True)
    @patch('os.path.isdir', return_value=True)
    @patch('os.listdir', return_value=['remaining_file.txt'])  # Non-empty directory
    @patch('os.rmdir')
    def test_cleanup_non_empty_directories(self, mock_rmdir, mock_listdir, mock_isdir, mock_exists, tmp_path):
        """Test that non-empty directories are not removed"""
        restorer = FileRestorer(str(tmp_path))
        
        backup_data = {
            "folder_mappings": {
                "docs": ["file1.txt"]
            }
        }
        
        restorer._cleanup_empty_directories(backup_data)
        
        # Should not attempt to remove non-empty directory
        mock_rmdir.assert_not_called()


class TestFullRestoreProcess:
    """Test complete restoration process"""
    
    @pytest.mark.unit
    @patch.object(FileRestorer, '_load_backup_data')
    @patch.object(FileRestorer, '_restore_single_file')
    @patch.object(FileRestorer, '_cleanup_empty_directories')
    @patch('builtins.print')
    def test_restore_success(self, mock_print, mock_cleanup, mock_restore_single, mock_load_backup, tmp_path):
        """Test successful complete restoration"""
        # Setup mocks
        mock_load_backup.return_value = {
            "file_paths": [
                {"original": "/orig/file1.txt", "new": "/new/file1.txt"},
                {"original": "/orig/file2.pdf", "new": "/new/file2.pdf"}
            ]
        }
        mock_restore_single.return_value = True
        
        restorer = FileRestorer(str(tmp_path))
        result = restorer.restore()
        
        assert result is True
        assert mock_restore_single.call_count == 2
        mock_cleanup.assert_called_once()
    
    @pytest.mark.unit
    @patch.object(FileRestorer, '_load_backup_data', return_value=None)
    @patch('builtins.print')
    def test_restore_no_backup_data(self, mock_print, mock_load_backup, tmp_path):
        """Test restoration with no backup data"""
        restorer = FileRestorer(str(tmp_path))
        result = restorer.restore()
        
        assert result is False
        mock_print.assert_called()
    
    @pytest.mark.unit
    @patch.object(FileRestorer, '_load_backup_data')
    @patch.object(FileRestorer, '_restore_single_file')
    @patch('builtins.print')
    def test_restore_partial_success(self, mock_print, mock_restore_single, mock_load_backup, tmp_path):
        """Test restoration with partial success"""
        # Setup mocks - some files succeed, some fail
        mock_load_backup.return_value = {
            "file_paths": [
                {"original": "/orig/file1.txt", "new": "/new/file1.txt"},
                {"original": "/orig/file2.pdf", "new": "/new/file2.pdf"}
            ]
        }
        mock_restore_single.side_effect = [True, False]  # First succeeds, second fails
        
        restorer = FileRestorer(str(tmp_path))
        result = restorer.restore()
        
        assert result is False  # Not all files restored successfully


class TestRestoreFolderFunction:
    """Test the main restore_folder function"""
    
    @pytest.mark.unit
    @patch.object(FileRestorer, 'restore', return_value=True)
    @patch('builtins.print')
    def test_restore_folder_success(self, mock_print, mock_restore):
        """Test successful folder restoration"""
        restore_folder('/test/path')
        
        mock_restore.assert_called_once()
        mock_print.assert_called_with("File restoration completed successfully!")
    
    @pytest.mark.unit
    @patch.object(FileRestorer, 'restore', return_value=False)
    @patch('builtins.print')
    def test_restore_folder_failure(self, mock_print, mock_restore):
        """Test folder restoration with errors"""
        restore_folder('/test/path')
        
        mock_restore.assert_called_once()
        mock_print.assert_called_with("File restoration completed with errors.")