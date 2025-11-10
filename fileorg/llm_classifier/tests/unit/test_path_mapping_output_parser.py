"""
Unit tests for PathMappingOutputParser.

Tests path assembly logic and JSON parsing.
"""

import json

import pytest

from fileorg.llm_classifier.application.path_mapping_output_parser import PathMappingOutputParser
from fileorg.llm_classifier.ports import FileMapping


class TestPathMappingOutputParser:
    """Test PathMappingOutputParser functionality."""

    def test_parse_simple_mapping(self):
        """Test basic path mapping parsing."""
        parser = PathMappingOutputParser()

        llm_output = """
        {
          "C:/test/report.pdf": {
            "category": "Financial Reports",
            "summary": "Q4 financial report",
            "reason": "Contains financial data and metrics"
          }
        }
        """

        result = parser.parse(llm_output)

        assert len(result) == 1
        assert "C:/test/report.pdf" in result

        mapping = result["C:/test/report.pdf"]
        assert isinstance(mapping, FileMapping)
        assert mapping.old_path == "C:/test/report.pdf"
        assert mapping.new_relative_path == "Financial_Reports/report.pdf"
        assert mapping.category == "Financial Reports"
        assert mapping.summary == "Q4 financial report"
        assert mapping.reason == "Contains financial data and metrics"

    def test_category_name_normalization(self):
        """Test that category names with spaces are normalized to underscores."""
        parser = PathMappingOutputParser()

        llm_output = """
        {
          "C:/file.txt": {
            "category": "My Important Documents",
            "summary": "Test document",
            "reason": "Test reason"
          }
        }
        """

        result = parser.parse(llm_output)
        mapping = result["C:/file.txt"]

        # new_relative_path should have underscores
        assert mapping.new_relative_path == "My_Important_Documents/file.txt"
        # Original category should preserve spaces
        assert mapping.category == "My Important Documents"

    def test_parse_multiple_files(self):
        """Test parsing multiple file mappings."""
        parser = PathMappingOutputParser()

        llm_output = """
        {
          "C:/Desktop/report.pdf": {
            "category": "Financial Reports",
            "summary": "Q4 earnings",
            "reason": "Financial document"
          },
          "C:/Downloads/script.py": {
            "category": "Python Scripts",
            "summary": "Data processing script",
            "reason": "Python code for automation"
          },
          "/home/user/notes.txt": {
            "category": "Personal Notes",
            "summary": "Meeting notes",
            "reason": "Personal documentation"
          }
        }
        """

        result = parser.parse(llm_output)

        assert len(result) == 3
        assert "C:/Desktop/report.pdf" in result
        assert "C:/Downloads/script.py" in result
        assert "/home/user/notes.txt" in result

        # Verify path assembly
        assert result["C:/Desktop/report.pdf"].new_relative_path == "Financial_Reports/report.pdf"
        assert result["C:/Downloads/script.py"].new_relative_path == "Python_Scripts/script.py"
        assert result["/home/user/notes.txt"].new_relative_path == "Personal_Notes/notes.txt"

    def test_parse_json_in_markdown_code_block(self):
        """Test extracting JSON from markdown code blocks."""
        parser = PathMappingOutputParser()

        llm_output = """
        Here's the categorization:

        ```json
        {
          "C:/file.txt": {
            "category": "Documents",
            "summary": "Test doc",
            "reason": "Document file"
          }
        }
        ```
        """

        result = parser.parse(llm_output)

        assert len(result) == 1
        assert "C:/file.txt" in result

    def test_parse_json_in_plain_code_block(self):
        """Test extracting JSON from plain code blocks."""
        parser = PathMappingOutputParser()

        llm_output = """
        ```
        {
          "C:/test.pdf": {
            "category": "Test Files",
            "summary": "Test file",
            "reason": "Testing"
          }
        }
        ```
        """

        result = parser.parse(llm_output)

        assert len(result) == 1
        assert result["C:/test.pdf"].new_relative_path == "Test_Files/test.pdf"

    def test_missing_required_field_raises_error(self):
        """Test that missing required fields raise ValueError."""
        parser = PathMappingOutputParser()

        # Missing 'summary' field
        llm_output = """
        {
          "C:/file.txt": {
            "category": "Documents",
            "reason": "Test reason"
          }
        }
        """

        with pytest.raises(ValueError, match="Missing required field 'summary'"):
            parser.parse(llm_output)

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        parser = PathMappingOutputParser()

        llm_output = """
        This is not JSON at all!
        Just some random text.
        """

        with pytest.raises(ValueError, match="Invalid JSON"):
            parser.parse(llm_output)

    def test_empty_response_raises_error(self):
        """Test that empty response raises ValueError."""
        parser = PathMappingOutputParser()

        with pytest.raises(ValueError, match="Empty response"):
            parser.parse("")

    def test_filename_extraction(self):
        """Test that filenames are correctly extracted from various path formats."""
        parser = PathMappingOutputParser()

        test_cases = {
            "C:/path/to/file.txt": "file.txt",
            "C:\\Windows\\path\\document.pdf": "document.pdf",
            "/unix/path/script.py": "script.py",
            "/Users/name/Desktop/report.xlsx": "report.xlsx",
        }

        for path, expected_filename in test_cases.items():
            # Use json.dumps to properly escape the path
            test_data = {
                path: {
                    "category": "Test",
                    "summary": "Test",
                    "reason": "Test",
                }
            }
            llm_output = json.dumps(test_data)

            result = parser.parse(llm_output)
            mapping = result[path]

            assert mapping.new_relative_path.endswith(expected_filename), f"Failed for {path}"

    def test_special_characters_in_category(self):
        """Test handling of special characters in category names."""
        parser = PathMappingOutputParser()

        llm_output = """
        {
          "C:/file.txt": {
            "category": "C++ Code Files",
            "summary": "C++ source code",
            "reason": "Contains C++ code"
          }
        }
        """

        result = parser.parse(llm_output)
        mapping = result["C:/file.txt"]

        # Spaces should be replaced with underscores
        # Other characters should be preserved
        assert mapping.new_relative_path == "C++_Code_Files/file.txt"
        assert mapping.category == "C++ Code Files"

    def test_preserve_file_extension(self):
        """Test that file extensions are preserved in new paths."""
        parser = PathMappingOutputParser()

        extensions = [".pdf", ".txt", ".py", ".xlsx", ".docx", ".jpg"]

        for ext in extensions:
            llm_output = f"""
            {{
              "C:/test/file{ext}": {{
                "category": "Test Category",
                "summary": "Test file",
                "reason": "Testing"
              }}
            }}
            """

            result = parser.parse(llm_output)
            mapping = result[f"C:/test/file{ext}"]

            assert mapping.new_relative_path == f"Test_Category/file{ext}"
            assert mapping.new_relative_path.endswith(ext)
