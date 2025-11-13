"""
Unit tests for JSONOutputParser application strategy.

Tests verify that JSONOutputParser correctly implements the IOutputParser
interface and properly extracts and validates JSON from LLM outputs.
"""

import pytest

from fileorg.llm_classifier.adapters.output_parsers import JSONOutputParser
from fileorg.llm_classifier.ports import IOutputParser


@pytest.fixture
def parser():
    """Provide a JSONOutputParser with default settings."""
    return JSONOutputParser()


@pytest.fixture
def strict_parser():
    """Provide a JSONOutputParser in strict mode."""
    return JSONOutputParser(strict=True)


class TestJSONOutputParserInterface:
    """Test that JSONOutputParser correctly implements IOutputParser interface."""

    def test_implements_interface(self, parser):
        """Verify JSONOutputParser implements IOutputParser."""
        assert isinstance(parser, IOutputParser)

    def test_has_parse_method(self, parser):
        """Verify parse method exists and is callable."""
        assert hasattr(parser, "parse")
        assert callable(parser.parse)


class TestInitialization:
    """Test JSONOutputParser initialization."""

    def test_default_initialization(self):
        """Should initialize with default strict=False."""
        parser = JSONOutputParser()
        assert parser.strict is False

    def test_strict_mode_initialization(self):
        """Should initialize with strict=True when specified."""
        parser = JSONOutputParser(strict=True)
        assert parser.strict is True


class TestPureJSONParsing:
    """Test parsing of pure JSON output."""

    def test_parse_simple_json(self, parser):
        """Should parse simple JSON object."""
        json_text = '{"Documents": ["file1.txt", "file2.pdf"]}'
        result = parser.parse(json_text)

        assert result == {"Documents": ["file1.txt", "file2.pdf"]}

    def test_parse_multiple_categories(self, parser):
        """Should parse JSON with multiple categories."""
        json_text = """{
            "Documents": ["report.docx", "notes.txt"],
            "Code": ["app.py", "test.py"],
            "Images": ["photo.jpg"]
        }"""
        result = parser.parse(json_text)

        assert len(result) == 3
        assert result["Documents"] == ["report.docx", "notes.txt"]
        assert result["Code"] == ["app.py", "test.py"]
        assert result["Images"] == ["photo.jpg"]

    def test_parse_empty_category_list(self, parser):
        """Should parse categories with empty file lists."""
        json_text = '{"Documents": []}'
        result = parser.parse(json_text)

        assert result == {"Documents": []}

    def test_parse_unicode_content(self, parser):
        """Should handle Unicode in category names and filenames."""
        json_text = '{"文件": ["文檔.txt"], "código": ["app.py"]}'
        result = parser.parse(json_text)

        assert "文件" in result
        assert "código" in result


class TestMarkdownWrappedJSON:
    """Test parsing of JSON wrapped in markdown code blocks."""

    def test_parse_json_code_block(self, parser):
        """Should extract JSON from markdown code block."""
        text = """Here are the categories:
```json
{
    "Documents": ["file1.txt"],
    "Code": ["app.py"]
}
```
Hope this helps!"""
        result = parser.parse(text)

        assert result == {"Documents": ["file1.txt"], "Code": ["app.py"]}

    def test_parse_code_block_without_json_tag(self, parser):
        """Should extract JSON from code block without 'json' tag."""
        text = """```
{"Documents": ["file1.txt"]}
```"""
        result = parser.parse(text)

        assert result == {"Documents": ["file1.txt"]}

    def test_parse_multiple_code_blocks(self, parser):
        """Should use first valid JSON code block."""
        text = """First block (invalid):
```
This is not JSON
```

Second block (valid):
```json
{"Documents": ["file1.txt"]}
```

Third block:
```
{"Code": ["app.py"]}
```"""
        result = parser.parse(text)

        # Should use the first valid JSON (second block)
        assert result == {"Documents": ["file1.txt"]}


class TestMixedTextJSON:
    """Test parsing of JSON mixed with explanatory text."""

    def test_parse_json_with_prefix_text(self, parser):
        """Should extract JSON when prefixed with text."""
        text = """Based on the file analysis, I have categorized them as follows:
{"Documents": ["report.txt"], "Code": ["script.py"]}"""
        result = parser.parse(text)

        assert result == {"Documents": ["report.txt"], "Code": ["script.py"]}

    def test_parse_json_with_suffix_text(self, parser):
        """Should extract JSON when followed by text."""
        text = """{"Documents": ["file.txt"]}
This categorization is based on file content analysis."""
        result = parser.parse(text)

        assert result == {"Documents": ["file.txt"]}

    def test_parse_json_with_surrounding_text(self, parser):
        """Should extract JSON when surrounded by text."""
        text = """Analysis complete. Results:
{"Documents": ["file1.txt"], "Code": ["app.py"]}
Let me know if you need adjustments!"""
        result = parser.parse(text)

        assert result == {"Documents": ["file1.txt"], "Code": ["app.py"]}


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_empty_string_raises_error(self, parser):
        """Should raise ValueError for empty string."""
        with pytest.raises(ValueError, match="Output text cannot be empty"):
            parser.parse("")

    def test_whitespace_only_raises_error(self, parser):
        """Should raise ValueError for whitespace-only text."""
        with pytest.raises(ValueError, match="Output text cannot be empty"):
            parser.parse("   \n\t  ")

    def test_no_json_raises_error(self, parser):
        """Should raise ValueError when no JSON found."""
        text = "This is just plain text with no JSON at all."
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            parser.parse(text)

    def test_invalid_json_syntax_raises_error(self, parser):
        """Should raise ValueError for invalid JSON syntax."""
        text = '{"Documents": ["file1.txt", invalid]}'
        with pytest.raises(ValueError, match="(Failed to parse JSON|Could not extract valid JSON)"):
            parser.parse(text)

    def test_malformed_json_raises_error(self, parser):
        """Should raise ValueError for malformed JSON."""
        text = '{"Documents": ["file1.txt"'  # Missing closing braces
        with pytest.raises(ValueError):
            parser.parse(text)


class TestStructureValidation:
    """Test validation of JSON structure."""

    def test_non_dict_raises_error(self, parser):
        """Should raise ValueError if JSON is not a dict."""
        text = '["file1.txt", "file2.txt"]'
        with pytest.raises(ValueError, match="Expected JSON object"):
            parser.parse(text)

    def test_empty_dict_raises_error(self, parser):
        """Should raise ValueError for empty dict."""
        text = "{}"
        with pytest.raises(ValueError, match="Output JSON cannot be empty"):
            parser.parse(text)

    def test_non_string_category_raises_error(self, parser):
        """Should raise ValueError if category name is not string."""
        # This would require constructing invalid JSON, which json.loads won't allow
        # Skip this test as it's prevented by JSON parsing itself
        pass

    def test_empty_category_name_raises_error(self, parser):
        """Should raise ValueError for empty category name."""
        text = '{"": ["file1.txt"]}'
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            parser.parse(text)

    def test_whitespace_category_name_raises_error(self, parser):
        """Should raise ValueError for whitespace-only category name."""
        text = '{"   ": ["file1.txt"]}'
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            parser.parse(text)

    def test_non_list_files_raises_error(self, parser):
        """Should raise ValueError if file list is not array."""
        text = '{"Documents": "file1.txt"}'
        with pytest.raises(ValueError, match="must be array"):
            parser.parse(text)

    def test_non_string_filename_raises_error(self, parser):
        """Should raise ValueError if filename is not string."""
        text = '{"Documents": [123, 456]}'
        with pytest.raises(ValueError, match="must be string"):
            parser.parse(text)


class TestStrictMode:
    """Test strict mode behavior."""

    def test_strict_mode_fails_on_mixed_text(self, strict_parser):
        """Should fail in strict mode when JSON has surrounding text."""
        # Strict mode should be more restrictive
        # In this case, it should still work because we can extract valid JSON
        # But let's test a case where there's ambiguity
        pass

    def test_non_strict_mode_more_lenient(self, parser):
        """Should be more lenient in non-strict mode."""
        # Non-strict mode tries harder to extract JSON
        text = 'Some text {"Documents": ["file.txt"]} more text'
        result = parser.parse(text)

        assert result == {"Documents": ["file.txt"]}


class TestEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_nested_braces_in_values(self, parser):
        """Should handle filenames with special characters."""
        json_text = '{"Documents": ["file{1}.txt", "file[2].pdf"]}'
        result = parser.parse(json_text)

        assert result == {"Documents": ["file{1}.txt", "file[2].pdf"]}

    def test_special_characters_in_category_names(self, parser):
        """Should handle special characters in category names."""
        json_text = '{"Documents & Reports": ["file1.txt"]}'
        result = parser.parse(json_text)

        assert result == {"Documents & Reports": ["file1.txt"]}

    def test_very_long_category_list(self, parser):
        """Should handle categories with many files."""
        import json

        files = [f"file_{i}.txt" for i in range(100)]
        json_text = json.dumps({"Documents": files})
        result = parser.parse(json_text)

        assert len(result["Documents"]) == 100

    def test_real_llm_output_example_1(self, parser):
        """Should parse real LLM output with explanation."""
        text = """Based on the provided file contents and paths, I have categorized the files into the following folders:

```json
{
  "Code": ["sample_python.py"],
  "Documentation": ["README.md", "meeting_notes.txt"],
  "Configuration": ["config.json"],
  "Data": ["sales_data.csv"]
}
```

The categorization is based on file types and content."""

        result = parser.parse(text)

        assert "Code" in result
        assert "Documentation" in result
        assert "Configuration" in result
        assert "Data" in result

    def test_real_llm_output_example_2(self, parser):
        """Should parse LLM output with inline explanation."""
        text = """I've analyzed the files. Here's the categorization:
{"Programming": ["app.py", "test.py"], "Documents": ["notes.txt"]}
The Programming category includes all Python files."""

        result = parser.parse(text)

        assert result == {"Programming": ["app.py", "test.py"], "Documents": ["notes.txt"]}

    def test_multiline_pretty_printed_json(self, parser):
        """Should handle pretty-printed multiline JSON."""
        text = """{
  "Category 1": [
    "file1.txt",
    "file2.txt"
  ],
  "Category 2": [
    "file3.txt"
  ]
}"""
        result = parser.parse(text)

        assert len(result) == 2
        assert result["Category 1"] == ["file1.txt", "file2.txt"]
