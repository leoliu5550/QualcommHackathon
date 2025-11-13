"""
Unit tests for PathMappingOutputParser.

Tests verify that PathMappingOutputParser correctly implements the IOutputParser
interface and properly parses LLM output to file path mappings.
"""

import json
from unittest.mock import patch

import pytest

from fileorg.llm_classifier.adapters.output_parsers import PathMappingOutputParser
from fileorg.llm_classifier.ports import IOutputParser
from fileorg.llm_classifier.ports.models import FileMapping


@pytest.fixture
def parser():
    """Provide a PathMappingOutputParser instance."""
    return PathMappingOutputParser()


@pytest.fixture
def valid_llm_output():
    """Provide valid LLM output for single file."""
    return json.dumps(
        {"C:/Desktop/report.pdf": {"category": "Financial Reports", "summary": "Q4 earnings report", "reason": "Contains financial data"}}
    )


@pytest.fixture
def valid_multiple_files_output():
    """Provide valid LLM output for multiple files."""
    return json.dumps(
        {
            "C:/Desktop/report.pdf": {"category": "Financial Reports", "summary": "Q4 earnings report", "reason": "Contains financial data"},
            "C:/Desktop/photo.jpg": {"category": "Personal Photos", "summary": "Family vacation photo", "reason": "Personal image file"},
            "C:/Desktop/script.py": {"category": "Code", "summary": "Python automation script", "reason": "Programming file"},
        }
    )


class TestPathMappingOutputParserInterface:
    """Test that PathMappingOutputParser correctly implements IOutputParser interface."""

    def test_implements_interface(self, parser):
        """Verify PathMappingOutputParser implements IOutputParser."""
        assert isinstance(parser, IOutputParser)

    def test_has_parse_method(self, parser):
        """Verify parse method exists and is callable."""
        assert hasattr(parser, "parse")
        assert callable(parser.parse)


class TestParseSuccessful:
    """Test successful parsing scenarios."""

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_single_file_mapping(self, mock_logger, parser, valid_llm_output):
        """Should parse single file mapping correctly."""
        result = parser.parse(valid_llm_output)

        assert isinstance(result, dict)
        assert len(result) == 1
        assert "C:/Desktop/report.pdf" in result

        mapping = result["C:/Desktop/report.pdf"]
        assert isinstance(mapping, FileMapping)
        assert mapping.old_path == "C:/Desktop/report.pdf"
        assert mapping.new_relative_path == "Financial_Reports/report.pdf"
        assert mapping.category == "Financial Reports"
        assert mapping.summary == "Q4 earnings report"
        assert mapping.reason == "Contains financial data"

        # Verify logging
        mock_logger.info.assert_called_once()
        assert "Successfully parsed 1 file mappings" in mock_logger.info.call_args[0][0]

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_multiple_file_mappings(self, mock_logger, parser, valid_multiple_files_output):
        """Should parse multiple file mappings correctly."""
        result = parser.parse(valid_multiple_files_output)

        assert isinstance(result, dict)
        assert len(result) == 3
        assert "C:/Desktop/report.pdf" in result
        assert "C:/Desktop/photo.jpg" in result
        assert "C:/Desktop/script.py" in result

        # Verify each mapping
        assert result["C:/Desktop/report.pdf"].category == "Financial Reports"
        assert result["C:/Desktop/photo.jpg"].category == "Personal Photos"
        assert result["C:/Desktop/script.py"].category == "Code"

        # Verify logging
        assert "Successfully parsed 3 file mappings" in mock_logger.info.call_args[0][0]

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_category_with_spaces(self, mock_logger, parser):
        """Should normalize category names with spaces to underscores."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": "Important Documents", "summary": "Important file", "reason": "High priority"}})

        result = parser.parse(llm_output)

        mapping = result["C:/test/file.txt"]
        assert mapping.category == "Important Documents"  # Original preserved
        assert mapping.new_relative_path == "Important_Documents/file.txt"  # Normalized

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_unicode_content(self, mock_logger, parser):
        """Should handle Unicode in paths and content."""
        llm_output = json.dumps(
            {"C:/文件/報告.pdf": {"category": "財務報告", "summary": "季度財務報告", "reason": "包含財務數據"}}, ensure_ascii=False
        )

        result = parser.parse(llm_output)

        assert "C:/文件/報告.pdf" in result
        mapping = result["C:/文件/報告.pdf"]
        assert mapping.category == "財務報告"
        assert mapping.new_relative_path == "財務報告/報告.pdf"

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_json_in_markdown_code_block(self, mock_logger, parser):
        """Should extract JSON from markdown code blocks."""
        llm_output = """Here are the file mappings:
```json
{
    "C:/Desktop/report.pdf": {
        "category": "Reports",
        "summary": "Annual report",
        "reason": "Business document"
    }
}
```
Hope this helps!"""

        result = parser.parse(llm_output)

        assert len(result) == 1
        assert "C:/Desktop/report.pdf" in result
        assert result["C:/Desktop/report.pdf"].category == "Reports"

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_unix_paths(self, mock_logger, parser):
        """Should handle Unix-style paths."""
        llm_output = json.dumps({"/home/user/document.txt": {"category": "Documents", "summary": "Personal document", "reason": "Text file"}})

        result = parser.parse(llm_output)

        assert "/home/user/document.txt" in result
        mapping = result["/home/user/document.txt"]
        assert mapping.new_relative_path == "Documents/document.txt"

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_complex_filename(self, mock_logger, parser):
        """Should handle complex filenames with special characters."""
        llm_output = json.dumps(
            {"C:/Desktop/report_2024_Q4_final_v2.pdf": {"category": "Reports", "summary": "Final Q4 report", "reason": "Business document"}}
        )

        result = parser.parse(llm_output)

        mapping = result["C:/Desktop/report_2024_Q4_final_v2.pdf"]
        assert mapping.new_relative_path == "Reports/report_2024_Q4_final_v2.pdf"

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_strips_whitespace_from_fields(self, mock_logger, parser):
        """Should strip whitespace from category, summary, and reason."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": "  Documents  ", "summary": "  Important file  ", "reason": "  Business use  "}})

        result = parser.parse(llm_output)

        mapping = result["C:/test/file.txt"]
        assert mapping.category == "Documents"
        assert mapping.summary == "Important file"
        assert mapping.reason == "Business use"


class TestValidateFields:
    """Test field validation."""

    def test_missing_category_raises_error(self, parser):
        """Should raise ValueError when category field is missing."""
        llm_output = json.dumps({"C:/test/file.txt": {"summary": "Test file", "reason": "Testing"}})

        with pytest.raises(ValueError, match="Missing required field 'category'"):
            parser.parse(llm_output)

    def test_missing_summary_raises_error(self, parser):
        """Should raise ValueError when summary field is missing."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": "Documents", "reason": "Testing"}})

        with pytest.raises(ValueError, match="Missing required field 'summary'"):
            parser.parse(llm_output)

    def test_missing_reason_raises_error(self, parser):
        """Should raise ValueError when reason field is missing."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": "Documents", "summary": "Test file"}})

        with pytest.raises(ValueError, match="Missing required field 'reason'"):
            parser.parse(llm_output)

    def test_empty_category_raises_error(self, parser):
        """Should raise ValueError when category is empty."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": "", "summary": "Test file", "reason": "Testing"}})

        with pytest.raises(ValueError, match="Invalid 'category' value"):
            parser.parse(llm_output)

    def test_whitespace_only_category_raises_error(self, parser):
        """Should raise ValueError when category is whitespace only."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": "   ", "summary": "Test file", "reason": "Testing"}})

        with pytest.raises(ValueError, match="Invalid 'category' value"):
            parser.parse(llm_output)

    def test_non_string_category_raises_error(self, parser):
        """Should raise ValueError when category is not a string."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": 123, "summary": "Test file", "reason": "Testing"}})

        with pytest.raises(ValueError, match="Invalid 'category' value"):
            parser.parse(llm_output)

    def test_empty_summary_raises_error(self, parser):
        """Should raise ValueError when summary is empty."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": "Documents", "summary": "", "reason": "Testing"}})

        with pytest.raises(ValueError, match="Invalid 'summary' value"):
            parser.parse(llm_output)

    def test_empty_reason_raises_error(self, parser):
        """Should raise ValueError when reason is empty."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": "Documents", "summary": "Test file", "reason": ""}})

        with pytest.raises(ValueError, match="Invalid 'reason' value"):
            parser.parse(llm_output)


class TestPathAssembly:
    """Test path assembly logic."""

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_assemble_windows_path(self, mock_logger, parser):
        """Should correctly assemble path from Windows absolute path."""
        llm_output = json.dumps({"C:\\Users\\John\\Desktop\\report.pdf": {"category": "Reports", "summary": "Annual report", "reason": "Business"}})

        result = parser.parse(llm_output)

        mapping = result["C:\\Users\\John\\Desktop\\report.pdf"]
        assert mapping.old_path == "C:\\Users\\John\\Desktop\\report.pdf"
        assert mapping.new_relative_path == "Reports/report.pdf"

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_category_normalization_multiple_spaces(self, mock_logger, parser):
        """Should normalize category with multiple spaces."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": "Very Important Documents", "summary": "Important", "reason": "Business"}})

        result = parser.parse(llm_output)

        mapping = result["C:/test/file.txt"]
        assert mapping.new_relative_path == "Very_Important_Documents/file.txt"
        assert mapping.category == "Very Important Documents"  # Original preserved

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_preserves_file_extension(self, mock_logger, parser):
        """Should preserve file extension in new path."""
        llm_output = json.dumps({"C:/test/document.docx": {"category": "Documents", "summary": "Word document", "reason": "Office file"}})

        result = parser.parse(llm_output)

        mapping = result["C:/test/document.docx"]
        assert mapping.new_relative_path.endswith(".docx")
        assert mapping.new_relative_path == "Documents/document.docx"


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_empty_text_raises_error(self, mock_logger, parser):
        """Should raise ValueError for empty text."""
        with pytest.raises(ValueError, match="Output text cannot be empty"):
            parser.parse("")

        # Verify error was logged
        assert mock_logger.error.called

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_whitespace_only_raises_error(self, mock_logger, parser):
        """Should raise ValueError for whitespace-only text."""
        with pytest.raises(ValueError, match="Output text cannot be empty"):
            parser.parse("   \n\t  ")

        # Verify error was logged
        assert mock_logger.error.called

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_no_json_raises_error(self, mock_logger, parser):
        """Should raise ValueError when no JSON found."""
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            parser.parse("This is just plain text with no JSON")

        # Verify error was logged
        assert mock_logger.error.called

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_invalid_json_syntax_raises_error(self, mock_logger, parser):
        """Should raise ValueError for invalid JSON syntax."""
        with pytest.raises(ValueError):
            parser.parse('{"C:/test/file.txt": invalid}')

        # Verify error was logged
        assert mock_logger.error.called

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_non_dict_json_raises_error(self, mock_logger, parser):
        """Should raise ValueError if JSON is not a dict."""
        with pytest.raises(ValueError, match="Expected JSON object"):
            parser.parse('["file1.txt", "file2.txt"]')

        # Verify error was logged
        assert mock_logger.error.called

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_validation_error_logged_and_raised(self, mock_logger, parser):
        """Should log and raise ValueError for validation errors."""
        llm_output = json.dumps(
            {
                "C:/test/file.txt": {
                    "category": "Documents"
                    # Missing summary and reason
                }
            }
        )

        with pytest.raises(ValueError, match="Missing required field"):
            parser.parse(llm_output)

        # Verify error was logged
        assert mock_logger.error.called
        error_message = mock_logger.error.call_args[0][0]
        assert "Path mapping parsing failed" in error_message


class TestLogging:
    """Test logging behavior."""

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_logs_successful_parse(self, mock_logger, parser, valid_llm_output):
        """Should log successful parsing with file count."""
        parser.parse(valid_llm_output)

        mock_logger.info.assert_called_once()
        info_message = mock_logger.info.call_args[0][0]
        assert "Successfully parsed" in info_message
        assert "file mappings" in info_message

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_logs_path_assembly(self, mock_logger, parser, valid_llm_output):
        """Should log each path assembly."""
        parser.parse(valid_llm_output)

        # Check debug logs for path assembly
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Assembled mapping" in msg for msg in debug_calls)

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_logs_errors(self, mock_logger, parser):
        """Should log errors during parsing."""
        with pytest.raises(ValueError):
            parser.parse("invalid input")

        mock_logger.error.assert_called()


class TestEdgeCases:
    """Test edge cases and complex scenarios."""

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_empty_mappings_dict(self, mock_logger, parser):
        """Should handle empty mappings dictionary."""
        llm_output = json.dumps({})

        result = parser.parse(llm_output)

        assert isinstance(result, dict)
        assert len(result) == 0
        assert "Successfully parsed 0 file mappings" in mock_logger.info.call_args[0][0]

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_category_with_special_characters(self, mock_logger, parser):
        """Should handle special characters in category names."""
        llm_output = json.dumps({"C:/test/file.txt": {"category": "Documents & Reports", "summary": "Mixed category", "reason": "Special chars"}})

        result = parser.parse(llm_output)

        mapping = result["C:/test/file.txt"]
        # Only spaces are normalized, other special chars preserved
        assert mapping.category == "Documents & Reports"
        assert mapping.new_relative_path == "Documents_&_Reports/file.txt"

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_long_file_path(self, mock_logger, parser):
        """Should handle very long file paths."""
        long_path = "C:/Users/VeryLongUsername/Documents/Projects/2024/Q4/Reports/Financial/Annual/report.pdf"
        llm_output = json.dumps({long_path: {"category": "Reports", "summary": "Annual report", "reason": "Business"}})

        result = parser.parse(llm_output)

        assert long_path in result
        assert result[long_path].new_relative_path == "Reports/report.pdf"

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_multiple_files_same_category(self, mock_logger, parser):
        """Should handle multiple files in the same category."""
        llm_output = json.dumps(
            {
                "C:/test/file1.txt": {"category": "Documents", "summary": "First file", "reason": "Document file"},
                "C:/test/file2.txt": {"category": "Documents", "summary": "Second file", "reason": "Document file"},
            }
        )

        result = parser.parse(llm_output)

        assert len(result) == 2
        assert result["C:/test/file1.txt"].new_relative_path == "Documents/file1.txt"
        assert result["C:/test/file2.txt"].new_relative_path == "Documents/file2.txt"

    @patch("fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser.logger")
    def test_parse_with_explanatory_text(self, mock_logger, parser):
        """Should extract JSON when surrounded by explanatory text."""
        llm_output = """Based on the file analysis, here are the mappings:

{
    "C:/Desktop/report.pdf": {
        "category": "Reports",
        "summary": "Annual report",
        "reason": "Business document"
    }
}

Let me know if you need any adjustments!"""

        result = parser.parse(llm_output)

        assert len(result) == 1
        assert "C:/Desktop/report.pdf" in result
