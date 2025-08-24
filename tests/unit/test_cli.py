"""
Test suite for FileOrg CLI module
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import sys

from fileorg import cli


class TestArgumentParsing:
    """Test CLI argument parsing"""
    
    @pytest.mark.unit
    def test_parse_arguments_basic(self):
        """Test basic argument parsing"""
        with patch('sys.argv', ['fileorg', '/test/path']):
            args = cli.parse_arguments()
            assert args.target_path == '/test/path'
            assert not args.preview
            assert not args.restore
    
    @pytest.mark.unit  
    def test_parse_arguments_preview(self):
        """Test preview mode argument"""
        with patch('sys.argv', ['fileorg', '/test/path', '--preview']):
            args = cli.parse_arguments()
            assert args.target_path == '/test/path'
            assert args.preview
            assert not args.restore
    
    @pytest.mark.unit
    def test_parse_arguments_restore(self):
        """Test restore mode argument"""
        with patch('sys.argv', ['fileorg', '/test/path', '--restore']):
            args = cli.parse_arguments()
            assert args.target_path == '/test/path'
            assert not args.preview
            assert args.restore
    
    @pytest.mark.unit
    def test_parse_arguments_conflicting_flags(self):
        """Test that conflicting flags are rejected"""
        with patch('sys.argv', ['fileorg', '/test/path', '--preview', '--restore']):
            with pytest.raises(SystemExit):
                cli.parse_arguments()


class TestBackupOperations:
    """Test backup-related operations"""
    
    @pytest.mark.unit
    def test_check_existing_backup_exists(self, tmp_path):
        """Test backup detection when backup exists"""
        backup_dir = tmp_path / ".backup"
        backup_dir.mkdir()
        backup_file = backup_dir / "file_paths.json"
        backup_file.write_text('{"test": "data"}')
        
        result = cli.check_existing_backup(str(tmp_path))
        assert result is True
    
    @pytest.mark.unit
    def test_check_existing_backup_not_exists(self, tmp_path):
        """Test backup detection when backup doesn't exist"""
        result = cli.check_existing_backup(str(tmp_path))
        assert result is False
    
    @pytest.mark.unit
    def test_load_backup_data_success(self, tmp_path):
        """Test successful backup data loading"""
        backup_dir = tmp_path / ".backup"
        backup_dir.mkdir()
        backup_file = backup_dir / "file_paths.json"
        test_data = {"file_paths": [{"original": "/a", "new": "/b"}]}
        backup_file.write_text(str(test_data).replace("'", '"'))
        
        result = cli.load_backup_data(str(tmp_path))
        assert result is not None
        assert "file_paths" in result
    
    @pytest.mark.unit
    def test_load_backup_data_missing_file(self, tmp_path):
        """Test backup data loading with missing file"""
        result = cli.load_backup_data(str(tmp_path))
        assert result is None


class TestPathNormalization:
    """Test cross-platform path handling"""
    
    @pytest.mark.unit
    @patch('fileorg.cli.os.path.exists')
    def test_main_path_normalization_windows(self, mock_exists):
        """Test Windows path normalization"""
        mock_exists.return_value = True
        
        with patch('sys.argv', ['fileorg', 'C:\\Users\\test\\docs']):
            with patch('fileorg.cli.run_standard_mode') as mock_run:
                cli.main()
                # Verify normalized path is passed
                mock_run.assert_called_once()
                called_path = mock_run.call_args[0][0]
                assert os.path.isabs(called_path)
    
    @pytest.mark.unit
    @patch('fileorg.cli.os.path.exists')
    def test_main_path_normalization_unix(self, mock_exists):
        """Test Unix path normalization"""
        mock_exists.return_value = True
        
        with patch('sys.argv', ['fileorg', '/home/user/docs']):
            with patch('fileorg.cli.run_standard_mode') as mock_run:
                cli.main()
                mock_run.assert_called_once()
                called_path = mock_run.call_args[0][0]
                assert os.path.isabs(called_path)
    
    @pytest.mark.unit
    def test_main_invalid_path(self):
        """Test handling of invalid paths"""
        with patch('sys.argv', ['fileorg', '/nonexistent/path']):
            with pytest.raises(SystemExit):
                cli.main()


class TestModeOperations:
    """Test different CLI operation modes"""
    
    @pytest.mark.unit
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.restore.restore_folder.restore_folder')
    def test_main_restore_mode(self, mock_restore, mock_exists):
        """Test restore mode execution"""
        with patch('sys.argv', ['fileorg', '/test/path', '--restore']):
            cli.main()
            mock_restore.assert_called_once()
    
    @pytest.mark.unit 
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.cli.run_preview_mode')
    def test_main_preview_mode(self, mock_preview, mock_exists):
        """Test preview mode execution"""
        with patch('sys.argv', ['fileorg', '/test/path', '--preview']):
            cli.main()
            mock_preview.assert_called_once()
    
    @pytest.mark.unit
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.cli.run_standard_mode')
    def test_main_standard_mode(self, mock_standard, mock_exists):
        """Test standard mode execution"""
        with patch('sys.argv', ['fileorg', '/test/path']):
            cli.main()
            mock_standard.assert_called_once()


class TestPreviewMode:
    """Test preview mode functionality"""
    
    @pytest.mark.unit
    @patch('fileorg.core.organizer.Organizer')
    @patch('os.makedirs')
    def test_run_preview_mode(self, mock_makedirs, mock_organizer_class):
        """Test preview mode execution"""
        # Setup mock organizer
        mock_organizer = Mock()
        mock_organizer._file_scanner.return_value = ['file1.txt', 'file2.pdf']
        mock_organizer._file_parser.return_value = {'summaries': []}
        mock_organizer._generate_folder.return_value = {
            'classification_time': '2.5s',
            'folder_mappings': {'Documents': ['file1.txt', 'file2.pdf']}
        }
        mock_organizer_class.return_value = mock_organizer
        
        result = cli.run_preview_mode('/test/path')
        
        # Verify organizer was configured and methods called
        assert mock_organizer.target_path == '/test/path'
        mock_organizer._file_scanner.assert_called_once()
        mock_organizer._file_parser.assert_called_once()
        mock_organizer._generate_folder.assert_called_once()
        assert 'folder_mappings' in result


class TestStandardMode:
    """Test standard mode functionality"""
    
    @pytest.mark.unit
    @patch('fileorg.cli.check_existing_backup', return_value=False)
    @patch('fileorg.core.organizer.Organizer')
    @patch('os.makedirs')
    def test_run_standard_mode_no_backup(self, mock_makedirs, mock_organizer_class, mock_check_backup):
        """Test standard mode without existing backup"""
        mock_organizer = Mock()
        mock_organizer_class.return_value = mock_organizer
        
        cli.run_standard_mode('/test/path')
        
        mock_organizer.start_organize.assert_called_once_with('/test/path')
    
    @pytest.mark.unit
    @patch('fileorg.cli.check_existing_backup', return_value=True)
    @patch('fileorg.cli.load_backup_data')
    @patch('fileorg.cli.apply_backup_structure')
    def test_run_standard_mode_with_backup(self, mock_apply_backup, mock_load_backup, mock_check_backup):
        """Test standard mode with existing backup"""
        mock_load_backup.return_value = {'file_paths': []}
        
        cli.run_standard_mode('/test/path')
        
        mock_apply_backup.assert_called_once()


class TestApplyBackupStructure:
    """Test backup structure application"""
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('shutil.move')
    def test_apply_backup_structure(self, mock_move, mock_makedirs, mock_exists):
        """Test applying backup structure"""
        backup_data = {
            "file_paths": [
                {"original": "/original/file1.txt", "new": "/organized/docs/file1.txt"},
                {"original": "/original/file2.pdf", "new": "/organized/docs/file2.pdf"}
            ]
        }
        
        cli.apply_backup_structure(backup_data)
        
        # Verify files were moved
        assert mock_move.call_count == 2
        mock_move.assert_any_call(
            os.path.normpath("/original/file1.txt"), 
            os.path.normpath("/organized/docs/file1.txt")
        )


class TestLoadBackupDataExtended:
    """Extended tests for load_backup_data function"""
    
    @pytest.mark.unit
    def test_load_backup_data_invalid_json(self, tmp_path):
        """Test backup data loading with invalid JSON"""
        backup_dir = tmp_path / ".backup"
        backup_dir.mkdir()
        backup_file = backup_dir / "file_paths.json"
        backup_file.write_text('{"invalid": json}')  # Invalid JSON
        
        with patch('builtins.print') as mock_print:
            result = cli.load_backup_data(str(tmp_path))
            
        assert result is None
        mock_print.assert_called_once()
        assert "載入備份資料時發生錯誤" in mock_print.call_args[0][0]
    
    @pytest.mark.unit
    def test_load_backup_data_permission_error(self, tmp_path):
        """Test backup data loading with permission error"""
        backup_dir = tmp_path / ".backup"
        backup_dir.mkdir()
        backup_file = backup_dir / "file_paths.json"
        backup_file.write_text('{"test": "data"}')
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with patch('builtins.print') as mock_print:
                result = cli.load_backup_data(str(tmp_path))
            
        assert result is None
        mock_print.assert_called_once()


class TestApplyBackupStructureExtended:
    """Extended tests for apply_backup_structure function"""
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=False)
    @patch('builtins.print')
    def test_apply_backup_structure_missing_files(self, mock_print, mock_exists):
        """Test applying backup when original files don't exist"""
        backup_data = {
            "file_paths": [
                {"original": "/missing/file1.txt", "new": "/organized/docs/file1.txt"}
            ]
        }
        
        cli.apply_backup_structure(backup_data)
        
        # Should print warning about missing files
        warning_calls = [call for call in mock_print.call_args_list 
                        if "找不到原始檔案" in str(call)]
        assert len(warning_calls) > 0
    
    @pytest.mark.unit
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs')
    @patch('shutil.move', side_effect=PermissionError("Access denied"))
    @patch('builtins.print')
    def test_apply_backup_structure_move_error(self, mock_print, mock_move, mock_makedirs, mock_exists):
        """Test applying backup when file move fails"""
        backup_data = {
            "file_paths": [
                {"original": "/original/file1.txt", "new": "/organized/docs/file1.txt"}
            ]
        }
        
        cli.apply_backup_structure(backup_data)
        
        # Should print error message about failed move
        error_calls = [call for call in mock_print.call_args_list 
                      if "移動失敗" in str(call)]
        assert len(error_calls) > 0
    
    @pytest.mark.unit
    def test_apply_backup_structure_empty_data(self):
        """Test applying backup with empty file paths"""
        backup_data = {"file_paths": []}
        
        with patch('builtins.print') as mock_print:
            cli.apply_backup_structure(backup_data)
        
        # Should still print summary with 0 files moved
        summary_calls = [call for call in mock_print.call_args_list 
                        if "已根據備份結構移動" in str(call)]
        assert len(summary_calls) > 0
        assert "0/0" in str(summary_calls[0])
    
    @pytest.mark.unit 
    @patch('os.path.exists', return_value=True)
    @patch('os.makedirs', side_effect=OSError("Permission denied"))
    @patch('builtins.print')
    def test_apply_backup_structure_mkdir_error(self, mock_print, mock_makedirs, mock_exists):
        """Test applying backup when directory creation fails"""
        backup_data = {
            "file_paths": [
                {"original": "/original/file1.txt", "new": "/restricted/docs/file1.txt"}
            ]
        }
        
        cli.apply_backup_structure(backup_data)
        
        # Should handle makedirs error gracefully
        error_calls = [call for call in mock_print.call_args_list 
                      if "移動失敗" in str(call)]
        assert len(error_calls) > 0


class TestRunPreviewModeExtended:
    """Extended tests for run_preview_mode function"""
    
    @pytest.mark.unit
    @patch('fileorg.core.organizer.Organizer')
    @patch('os.makedirs', side_effect=OSError("Permission denied"))
    @patch('builtins.print')
    def test_run_preview_mode_makedirs_error(self, mock_print, mock_makedirs, mock_organizer_class):
        """Test preview mode when backup directory creation fails"""
        with pytest.raises(OSError):
            cli.run_preview_mode('/test/path')
    
    @pytest.mark.unit
    @patch('fileorg.core.organizer.Organizer')
    @patch('os.makedirs')
    def test_run_preview_mode_organizer_error(self, mock_makedirs, mock_organizer_class):
        """Test preview mode when organizer operations fail"""
        mock_organizer = Mock()
        mock_organizer._file_scanner.side_effect = Exception("Scanner failed")
        mock_organizer_class.return_value = mock_organizer
        
        with pytest.raises(Exception):
            cli.run_preview_mode('/test/path')
    
    @pytest.mark.unit
    @patch('fileorg.core.organizer.Organizer')
    @patch('os.makedirs')
    def test_run_preview_mode_empty_results(self, mock_makedirs, mock_organizer_class):
        """Test preview mode with empty scanner results"""
        mock_organizer = Mock()
        mock_organizer._file_scanner.return_value = []
        mock_organizer._file_parser.return_value = {'summaries': []}
        mock_organizer._generate_folder.return_value = {
            'classification_time': '0.1s',
            'folder_mappings': {}
        }
        mock_organizer_class.return_value = mock_organizer
        
        result = cli.run_preview_mode('/test/path')
        
        assert 'folder_mappings' in result
        assert result['folder_mappings'] == {}


class TestRunStandardModeExtended:
    """Extended tests for run_standard_mode function"""
    
    @pytest.mark.unit
    @patch('fileorg.cli.check_existing_backup', return_value=True)
    @patch('fileorg.cli.load_backup_data', return_value=None)
    @patch('fileorg.core.organizer.Organizer')
    @patch('os.makedirs')
    @patch('builtins.print')
    def test_run_standard_mode_corrupted_backup(self, mock_print, mock_makedirs, mock_organizer_class, mock_load_backup, mock_check_backup):
        """Test standard mode with corrupted backup file"""
        mock_organizer = Mock()
        mock_organizer_class.return_value = mock_organizer
        
        cli.run_standard_mode('/test/path')
        
        # Should print corrupted backup message
        corrupted_calls = [call for call in mock_print.call_args_list 
                          if "備份檔案損壞或空白" in str(call)]
        assert len(corrupted_calls) > 0
        
        # Should still run full organizer
        mock_organizer.start_organize.assert_called_once_with('/test/path')
    
    @pytest.mark.unit
    @patch('fileorg.cli.check_existing_backup', return_value=False)
    @patch('fileorg.core.organizer.Organizer')
    @patch('os.makedirs', side_effect=OSError("Permission denied"))
    def test_run_standard_mode_makedirs_error(self, mock_makedirs, mock_organizer_class, mock_check_backup):
        """Test standard mode when backup directory creation fails"""
        with pytest.raises(OSError):
            cli.run_standard_mode('/test/path')
    
    @pytest.mark.unit
    @patch('fileorg.cli.check_existing_backup', return_value=False)
    @patch('fileorg.core.organizer.Organizer')
    @patch('os.makedirs')
    def test_run_standard_mode_organizer_error(self, mock_makedirs, mock_organizer_class, mock_check_backup):
        """Test standard mode when organizer fails"""
        mock_organizer = Mock()
        mock_organizer.start_organize.side_effect = Exception("Organizer failed")
        mock_organizer_class.return_value = mock_organizer
        
        with pytest.raises(Exception):
            cli.run_standard_mode('/test/path')


class TestMainFunctionExtended:
    """Extended tests for main function"""
    
    @pytest.mark.unit
    @patch('fileorg.cli.parse_arguments')
    def test_main_parse_arguments_error(self, mock_parse):
        """Test main when argument parsing fails"""
        mock_parse.side_effect = SystemExit(2)
        
        with pytest.raises(SystemExit):
            cli.main()
    
    @pytest.mark.unit
    @patch('sys.argv', ['fileorg', '/test/path'])
    @patch('fileorg.cli.os.path.exists', return_value=False)
    @patch('builtins.print')
    def test_main_nonexistent_path_message(self, mock_print, mock_exists):
        """Test main prints correct error message for nonexistent path"""
        with pytest.raises(SystemExit):
            cli.main()
        
        error_calls = [call for call in mock_print.call_args_list 
                      if "不存在" in str(call)]
        assert len(error_calls) > 0
    
    @pytest.mark.unit
    @patch('sys.argv', ['fileorg', 'relative/path'])
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.cli.run_standard_mode')
    def test_main_relative_path_normalization(self, mock_run_standard, mock_exists):
        """Test main normalizes relative paths to absolute"""
        cli.main()
        
        # Should call with absolute path
        called_path = mock_run_standard.call_args[0][0]
        assert os.path.isabs(called_path)
    
    @pytest.mark.unit
    @patch('sys.argv', ['fileorg', '/test/path'])
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.cli.run_standard_mode', side_effect=Exception("Test error"))
    @patch('builtins.print')
    @patch('traceback.print_exc')
    def test_main_exception_handling(self, mock_traceback, mock_print, mock_run_standard, mock_exists):
        """Test main handles exceptions properly"""
        with pytest.raises(SystemExit):
            cli.main()
        
        # Should print error message
        error_calls = [call for call in mock_print.call_args_list 
                      if "執行過程中發生錯誤" in str(call)]
        assert len(error_calls) > 0
        
        # Should print traceback
        mock_traceback.assert_called_once()
    
    @pytest.mark.unit
    @patch('sys.argv', ['fileorg', '/test/path', '--restore'])
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.restore.restore_folder.restore_folder')
    def test_main_restore_mode_execution(self, mock_restore, mock_exists):
        """Test main executes restore mode correctly"""
        cli.main()
        
        mock_restore.assert_called_once()
        # Should pass normalized absolute path
        called_path = mock_restore.call_args[0][0]
        assert os.path.isabs(called_path)
    
    @pytest.mark.unit
    @patch('sys.argv', ['fileorg', '/test/path', '--preview'])
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.cli.run_preview_mode')
    def test_main_preview_mode_execution(self, mock_preview, mock_exists):
        """Test main executes preview mode correctly"""
        cli.main()
        
        mock_preview.assert_called_once()
        # Should pass normalized absolute path
        called_path = mock_preview.call_args[0][0]
        assert os.path.isabs(called_path)


class TestArgumentParsingEdgeCases:
    """Test edge cases for argument parsing"""
    
    @pytest.mark.unit
    def test_parse_arguments_help_flag(self):
        """Test that help flag works correctly"""
        with patch('sys.argv', ['fileorg', '--help']):
            with pytest.raises(SystemExit):
                cli.parse_arguments()
    
    @pytest.mark.unit
    def test_parse_arguments_no_arguments(self):
        """Test parsing with no target path"""
        with patch('sys.argv', ['fileorg']):
            with pytest.raises(SystemExit):
                cli.parse_arguments()
    
    @pytest.mark.unit
    def test_parse_arguments_multiple_paths(self):
        """Test parsing with multiple paths (should only use first)"""
        with patch('sys.argv', ['fileorg', '/path1', '/path2']):
            with pytest.raises(SystemExit):
                cli.parse_arguments()


class TestCrossplatformPathHandling:
    """Test cross-platform path handling"""
    
    @pytest.mark.unit
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.cli.run_standard_mode')
    def test_main_windows_path_handling(self, mock_run_standard, mock_exists):
        """Test Windows-style paths are handled correctly"""
        windows_path = 'C:\\Users\\test\\Documents'
        
        with patch('sys.argv', ['fileorg', windows_path]):
            cli.main()
        
        called_path = mock_run_standard.call_args[0][0]
        assert os.path.isabs(called_path)
        # Path should be normalized
        assert called_path == os.path.abspath(os.path.normpath(windows_path))
    
    @pytest.mark.unit
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.cli.run_standard_mode')
    def test_main_unix_path_handling(self, mock_run_standard, mock_exists):
        """Test Unix-style paths are handled correctly"""
        unix_path = '/home/user/documents'
        
        with patch('sys.argv', ['fileorg', unix_path]):
            cli.main()
        
        called_path = mock_run_standard.call_args[0][0]
        assert os.path.isabs(called_path)
        # Path should be normalized
        assert called_path == os.path.abspath(os.path.normpath(unix_path))
    
    @pytest.mark.unit
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.cli.run_standard_mode')
    def test_main_path_with_spaces(self, mock_run_standard, mock_exists):
        """Test paths with spaces are handled correctly"""
        path_with_spaces = '/path with spaces/to folder'
        
        with patch('sys.argv', ['fileorg', path_with_spaces]):
            cli.main()
        
        called_path = mock_run_standard.call_args[0][0]
        assert os.path.isabs(called_path)
        assert 'with spaces' in called_path
    
    @pytest.mark.unit
    @patch('fileorg.cli.os.path.exists', return_value=True)
    @patch('fileorg.cli.run_standard_mode')
    def test_main_path_normalization_edge_cases(self, mock_run_standard, mock_exists):
        """Test path normalization edge cases"""
        # Path with double slashes
        messy_path = '//path//with//double//slashes//'
        
        with patch('sys.argv', ['fileorg', messy_path]):
            cli.main()
        
        called_path = mock_run_standard.call_args[0][0]
        assert '//' not in called_path or called_path.startswith('//')  # Allow UNC paths on Windows


class TestBackupOperationsEdgeCases:
    """Test edge cases for backup operations"""
    
    @pytest.mark.unit
    def test_check_existing_backup_nested_path(self, tmp_path):
        """Test backup detection with nested directory structure"""
        nested_path = tmp_path / "level1" / "level2" / "level3"
        nested_path.mkdir(parents=True)
        backup_dir = nested_path / ".backup"
        backup_dir.mkdir()
        backup_file = backup_dir / "file_paths.json"
        backup_file.write_text('{"test": "data"}')
        
        result = cli.check_existing_backup(str(nested_path))
        assert result is True
    
    @pytest.mark.unit
    def test_check_existing_backup_permission_error(self, tmp_path):
        """Test backup detection when permission error occurs"""
        # Create backup dir but make it inaccessible
        backup_dir = tmp_path / ".backup" 
        backup_dir.mkdir()
        
        with patch('os.path.exists', side_effect=PermissionError("Access denied")):
            # Should handle gracefully and return False
            result = cli.check_existing_backup(str(tmp_path))
            assert result is False