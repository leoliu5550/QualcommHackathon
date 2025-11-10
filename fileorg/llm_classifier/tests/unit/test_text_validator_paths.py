"""
Unit tests for BasicTextValidator path validation functionality.

Tests the new path validation methods.
"""

import pytest

from fileorg.llm_classifier.application.text_validator import BasicTextValidator


class TestBasicTextValidatorPaths:
    """Test path validation in BasicTextValidator."""

    def test_validate_path_valid_windows_path(self):
        """Test that valid Windows paths are accepted."""
        validator = BasicTextValidator()

        valid_paths = [
            "C:/Users/USER/Desktop/file.txt",
            "C:\\Users\\USER\\Documents\\report.pdf",
            "C:/path/to/script.py",
        ]

        for path in valid_paths:
            assert validator.validate_path(path), f"Should accept: {path}"

    def test_validate_path_valid_unix_path(self):
        """Test that valid Unix paths are accepted."""
        validator = BasicTextValidator()

        valid_paths = [
            "/home/user/file.txt",
            "/Users/name/Desktop/report.pdf",
            "/mnt/data/script.py",
        ]

        for path in valid_paths:
            assert validator.validate_path(path), f"Should accept: {path}"

    def test_validate_path_reject_relative_path(self):
        """Test that relative paths are rejected."""
        validator = BasicTextValidator()

        relative_paths = [
            "relative/path/file.txt",
            "./file.txt",
            "../parent/file.txt",
            "file.txt",
            "Documents/report.pdf",
        ]

        for path in relative_paths:
            assert not validator.validate_path(path), f"Should reject: {path}"

    def test_validate_path_reject_empty(self):
        """Test that empty paths are rejected."""
        validator = BasicTextValidator()

        assert not validator.validate_path("")
        assert not validator.validate_path("   ")
        assert not validator.validate_path(None)

    def test_validate_path_reject_directory_only(self):
        """Test that paths without filename are rejected."""
        validator = BasicTextValidator()

        directory_paths = [
            "C:/path/to/",
            "/home/user/",
        ]

        for path in directory_paths:
            assert not validator.validate_path(path), f"Should reject: {path}"

    def test_validate_paths_dict_valid(self):
        """Test that valid paths dictionary is accepted."""
        validator = BasicTextValidator()

        valid_dict = {
            "C:/Desktop/report.pdf": "Financial report content",
            "C:/Downloads/script.py": "import pandas as pd",
            "/home/user/notes.txt": "Meeting notes",
        }

        assert validator.validate_paths_dict(valid_dict)

    def test_validate_paths_dict_empty(self):
        """Test that empty dictionary is rejected."""
        validator = BasicTextValidator()

        assert not validator.validate_paths_dict({})
        assert not validator.validate_paths_dict(None)

    def test_validate_paths_dict_invalid_path(self):
        """Test that dictionary with invalid path is rejected."""
        validator = BasicTextValidator()

        invalid_dict = {
            "relative/path.txt": "content",  # Relative path
            "C:/valid/path.pdf": "content",
        }

        assert not validator.validate_paths_dict(invalid_dict)

    def test_validate_paths_dict_invalid_content_type(self):
        """Test that non-string content values are rejected."""
        validator = BasicTextValidator()

        invalid_dict = {
            "C:/path/file.txt": 12345,  # Integer instead of string
        }

        assert not validator.validate_paths_dict(invalid_dict)

    def test_validate_paths_dict_allow_empty_content(self):
        """Test that empty content strings are allowed."""
        validator = BasicTextValidator()

        dict_with_empty_content = {
            "C:/path/empty_file.txt": "",
            "C:/path/file.txt": "Some content",
        }

        # Empty content is allowed (some files might be empty)
        assert validator.validate_paths_dict(dict_with_empty_content)

    def test_validate_path_with_special_characters(self):
        """Test paths with special characters in filename."""
        validator = BasicTextValidator()

        paths_with_special_chars = [
            "C:/path/file name with spaces.txt",
            "C:/path/file-with-dashes.pdf",
            "C:/path/file_with_underscores.py",
            "C:/path/file.multiple.dots.txt",
        ]

        for path in paths_with_special_chars:
            assert validator.validate_path(path), f"Should accept: {path}"

    def test_validate_path_mixed_slashes(self):
        """Test that both forward and backward slashes work."""
        validator = BasicTextValidator()

        # Windows-style backslashes
        assert validator.validate_path("C:\\Users\\file.txt")

        # Unix-style forward slashes
        assert validator.validate_path("C:/Users/file.txt")

    def test_validate_paths_dict_not_dict_type(self):
        """Test that non-dictionary types are rejected."""
        validator = BasicTextValidator()

        assert not validator.validate_paths_dict("not a dict")
        assert not validator.validate_paths_dict([("C:/file.txt", "content")])
        assert not validator.validate_paths_dict(123)
