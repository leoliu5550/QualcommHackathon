"""
Unit tests for SummaryOutputParser.
"""

import json

import pytest

from fileorg.llm_classifier.adapters.output_parsers import SummaryOutputParser
from fileorg.llm_classifier.ports.models import FileSummary


@pytest.fixture
def parser():
    """Create SummaryOutputParser instance."""
    return SummaryOutputParser()


class TestSummaryOutputParser:
    """Test suite for SummaryOutputParser."""

    def test_parse_valid_keyword(self, parser):
        """Test parsing valid keyword from LLM output."""
        llm_output = json.dumps({"C:/test.pdf": "財務報告"})
        file_path = "C:/test.pdf"

        summary = parser.parse(llm_output, file_path=file_path)

        assert isinstance(summary, FileSummary)
        assert summary.file_path == file_path
        assert summary.summary == "財務報告"
        assert summary.metadata is not None
        assert "keyword_length" in summary.metadata

    def test_parse_with_markdown_code_block(self, parser):
        """Test parsing with markdown code block."""
        llm_output = """
        Here is the keyword:
        ```json
        {"C:/test.pdf": "會議紀錄"}
        ```
        """
        file_path = "C:/test.pdf"

        summary = parser.parse(llm_output, file_path=file_path)

        assert summary.file_path == file_path
        assert summary.summary == "會議紀錄"

    def test_parse_multiple_files_without_specifying_path(self, parser):
        """Test parsing returns first file when path not specified."""
        llm_output = json.dumps({"C:/file1.pdf": "keyword1", "C:/file2.txt": "keyword2"})

        summary = parser.parse(llm_output)

        # Should return the first file
        assert summary.file_path in ["C:/file1.pdf", "C:/file2.txt"]
        assert summary.summary in ["keyword1", "keyword2"]

    def test_parse_file_path_not_found(self, parser):
        """Test parsing fails when specified file_path not in output."""
        llm_output = json.dumps({"C:/test.pdf": "keyword"})
        wrong_path = "C:/other.pdf"

        with pytest.raises(ValueError, match="File path .* not found in LLM output"):
            parser.parse(llm_output, file_path=wrong_path)

    def test_parse_invalid_json(self, parser):
        """Test parsing fails with invalid JSON."""
        invalid_output = "not a json string"

        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            parser.parse(invalid_output, file_path="C:/test.pdf")

    def test_parse_empty_keyword(self, parser):
        """Test parsing fails with empty keyword."""
        llm_output = json.dumps({"C:/test.pdf": ""})

        with pytest.raises(ValueError, match="Invalid keyword.*must be non-empty"):
            parser.parse(llm_output, file_path="C:/test.pdf")

    def test_parse_keyword_with_warning(self, parser):
        """Test parsing issues warning for too many words."""
        # 4 words should trigger warning but still succeed
        llm_output = json.dumps({"C:/test.pdf": "這是一個很長的關鍵字"})
        file_path = "C:/test.pdf"

        # Should succeed but log warning
        summary = parser.parse(llm_output, file_path=file_path)
        assert summary.summary == "這是一個很長的關鍵字"

    def test_parse_metadata_inclusion(self, parser):
        """Test metadata is correctly populated."""
        llm_output = json.dumps({"C:/test.pdf": "keyword"})
        file_path = "C:/test.pdf"
        raw_length = 1000

        summary = parser.parse(llm_output, file_path=file_path, raw_length=raw_length)

        assert summary.metadata["raw_length"] == raw_length
        assert summary.metadata["keyword_length"] == 1
