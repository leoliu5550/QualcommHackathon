"""
Unit tests for BasicPromptBuilder adapter.

Tests verify that BasicPromptBuilder correctly implements the IPromptBuilder
interface and produces valid chat-formatted prompts for file classification.
"""

import json

import pytest

from fileorg.llm_classifier.adapters.prompt_builder import BasicPromptBuilder
from fileorg.llm_classifier.ports import IPromptBuilder


@pytest.fixture
def sample_file_data_single():
    """Provide sample JSON data with a single file."""
    return json.dumps({"report.pdf": {"path": "/documents/report.pdf", "content": "Annual sales report for Q4 2024"}})


@pytest.fixture
def sample_file_data_batch():
    """Provide sample JSON data with multiple files."""
    return json.dumps(
        {
            "analysis.pdf": {"path": "/stats/analysis.pdf", "content": "Statistical analysis of customer data using regression models"},
            "meeting_notes.docx": {"path": "/docs/meeting_notes.docx", "content": "Meeting notes from team sync on 2024-01-15"},
            "data.csv": {"path": "/data/data.csv", "content": "timestamp,value,category\n2024-01-01,100,A\n"},
        }
    )


@pytest.fixture
def sample_file_data_chinese():
    """Provide sample JSON data with Chinese filenames and content."""
    return json.dumps(
        {
            "學生自學計劃.docx": {"path": "/文檔/學生自學計劃.docx", "content": "學生自主學習計劃書"},
            "統計分析.pdf": {"path": "/統計/統計分析.pdf", "content": "主成分分析原理與應用"},
        }
    )


class TestBasicPromptBuilderInterface:
    """Test that BasicPromptBuilder correctly implements IPromptBuilder interface."""

    def test_implements_interface(self, prompt_builder):
        """Verify BasicPromptBuilder implements IPromptBuilder."""
        assert isinstance(prompt_builder, IPromptBuilder)

    def test_has_build_prompt_method(self, prompt_builder):
        """Verify build_prompt method exists and is callable."""
        assert hasattr(prompt_builder, "build_prompt")
        assert callable(prompt_builder.build_prompt)

    def test_has_correct_signature(self, prompt_builder, sample_file_data_single):
        """Verify build_prompt method accepts correct parameters."""
        # Should accept text, instruction, and max_tokens parameters
        result = prompt_builder.build_prompt(text=sample_file_data_single, instruction="Classify files", max_tokens=150000)
        assert result is not None


class TestBuildPromptMethod:
    """Test build_prompt() method behavior and output format."""

    def test_returns_list_of_dicts(self, prompt_builder, sample_file_data_single):
        """Should return a list of message dictionaries."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify these files")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(msg, dict) for msg in result)

    def test_messages_have_required_keys(self, prompt_builder, sample_file_data_single):
        """Each message should have 'role' and 'content' keys."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify these files")
        for msg in result:
            assert "role" in msg
            assert "content" in msg
            assert isinstance(msg["role"], str)
            assert isinstance(msg["content"], str)

    def test_has_system_and_user_messages(self, prompt_builder, sample_file_data_single):
        """Should contain at least one system message and one user message."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify these files")
        roles = [msg["role"] for msg in result]
        assert "system" in roles
        assert "user" in roles

    def test_system_message_first(self, prompt_builder, sample_file_data_single):
        """System message should come before user message."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify these files")
        assert result[0]["role"] == "system"

    def test_user_message_contains_instruction(self, prompt_builder, sample_file_data_single):
        """User message should contain the provided instruction."""
        instruction = "Organize files by category"
        result = prompt_builder.build_prompt(sample_file_data_single, instruction)
        user_messages = [msg for msg in result if msg["role"] == "user"]
        assert any(instruction in msg["content"] for msg in user_messages)

    def test_user_message_contains_file_data(self, prompt_builder, sample_file_data_batch):
        """User message should contain file data."""
        result = prompt_builder.build_prompt(sample_file_data_batch, "Classify files")
        user_messages = [msg for msg in result if msg["role"] == "user"]
        # Should contain at least one filename from the data
        assert any("analysis.pdf" in msg["content"] for msg in user_messages)


class TestJSONInputHandling:
    """Test handling of JSON-formatted file data."""

    def test_accepts_valid_json_string(self, prompt_builder, sample_file_data_single):
        """Should accept valid JSON string without errors."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify")
        assert result is not None

    def test_rejects_invalid_json(self, prompt_builder):
        """Should raise ValueError for invalid JSON input."""
        invalid_json = "This is not JSON {invalid"
        with pytest.raises(ValueError, match="valid JSON format"):
            prompt_builder.build_prompt(invalid_json, "Classify")

    def test_handles_empty_json_object(self, prompt_builder):
        """Should handle empty JSON object."""
        empty_json = json.dumps({})
        result = prompt_builder.build_prompt(empty_json, "Classify")
        assert result is not None

    def test_handles_nested_json_structure(self, prompt_builder):
        """Should handle nested JSON structures in file data."""
        nested_json = json.dumps({"file.txt": {"path": "/path", "content": "text", "metadata": {"author": "user", "date": "2024-01-01"}}})
        result = prompt_builder.build_prompt(nested_json, "Classify")
        assert result is not None


class TestSuggestedCategories:
    """Test handling of suggested categories configuration."""

    def test_initialization_without_categories(self):
        """Should initialize successfully without suggested categories."""
        builder = BasicPromptBuilder()
        assert builder.suggested_categories == []

    def test_initialization_with_categories(self):
        """Should store provided suggested categories."""
        categories = ["Documents", "Images", "Code"]
        builder = BasicPromptBuilder(suggested_categories=categories)
        assert builder.suggested_categories == categories

    def test_system_prompt_includes_suggested_categories(self, sample_file_data_single):
        """System prompt should mention suggested categories when provided."""
        categories = ["Documents", "Statistics", "Media"]
        builder = BasicPromptBuilder(suggested_categories=categories)
        result = builder.build_prompt(sample_file_data_single, "Classify")
        system_message = next(msg for msg in result if msg["role"] == "system")
        # Check if at least one category appears in system prompt
        assert any(cat in system_message["content"] for cat in categories)

    def test_system_prompt_without_suggested_categories(self, prompt_builder, sample_file_data_single):
        """System prompt should work without suggested categories."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify")
        system_message = next(msg for msg in result if msg["role"] == "system")
        assert "dynamically" in system_message["content"].lower() or "dynamic" in system_message["content"].lower()


class TestBilingualSupport:
    """Test Chinese and English bilingual support."""

    def test_system_prompt_contains_english(self, prompt_builder, sample_file_data_single):
        """System prompt should contain English instructions."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify")
        system_message = next(msg for msg in result if msg["role"] == "system")
        # Check for common English keywords
        english_keywords = ["file", "category", "classify", "organize"]
        assert any(keyword.lower() in system_message["content"].lower() for keyword in english_keywords)

    def test_system_prompt_contains_chinese(self, prompt_builder, sample_file_data_single):
        """System prompt should contain Chinese instructions."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify")
        system_message = next(msg for msg in result if msg["role"] == "system")
        # Check for Chinese characters (Unicode range)
        assert any("\u4e00" <= char <= "\u9fff" for char in system_message["content"])

    def test_handles_chinese_filenames(self, prompt_builder, sample_file_data_chinese):
        """Should correctly handle Chinese filenames in file data."""
        result = prompt_builder.build_prompt(sample_file_data_chinese, "分類這些文件")
        user_messages = [msg for msg in result if msg["role"] == "user"]
        # Should contain Chinese filename (may be Unicode-escaped in JSON)
        user_content = user_messages[0]["content"]
        # Check if either the literal Chinese characters or the file key appears
        assert "學生自學計劃" in user_content or "docx" in user_content

    def test_handles_chinese_instruction(self, prompt_builder, sample_file_data_single):
        """Should correctly handle Chinese instructions."""
        instruction = "將這些文件分類到有意義的類別中"
        result = prompt_builder.build_prompt(sample_file_data_single, instruction)
        user_messages = [msg for msg in result if msg["role"] == "user"]
        assert any(instruction in msg["content"] for msg in user_messages)


class TestTokenLimitHandling:
    """Test token limit and text truncation behavior."""

    def test_respects_max_tokens_parameter(self, prompt_builder):
        """Should truncate text when it exceeds max_tokens."""
        # Create a large JSON string
        large_content = "A" * 100000
        large_json = json.dumps({"large_file.txt": {"path": "/path", "content": large_content}})

        max_tokens = 1000
        result = prompt_builder.build_prompt(large_json, "Classify", max_tokens=max_tokens)

        # Check that result was generated (no errors)
        assert result is not None
        # User message shouldn't be excessively long (rough check: max_tokens * 4 chars + overhead)
        user_message = next(msg for msg in result if msg["role"] == "user")
        assert len(user_message["content"]) < max_tokens * 5  # Allow some overhead

    def test_handles_small_max_tokens(self, prompt_builder, sample_file_data_single):
        """Should handle very small max_tokens values."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify", max_tokens=10)
        assert result is not None

    def test_default_max_tokens(self, prompt_builder, sample_file_data_single):
        """Should use default max_tokens when not specified."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify")
        assert result is not None


class TestOutputFormatRequirements:
    """Test that system prompt specifies correct output format."""

    def test_system_prompt_specifies_json_format(self, prompt_builder, sample_file_data_single):
        """System prompt should specify JSON output format."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify")
        system_message = next(msg for msg in result if msg["role"] == "system")
        assert "json" in system_message["content"].lower()

    def test_system_prompt_shows_example_format(self, prompt_builder, sample_file_data_single):
        """System prompt should include example output format."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify")
        system_message = next(msg for msg in result if msg["role"] == "system")
        # Should contain example with category and file list structure
        assert "{" in system_message["content"]
        assert ":" in system_message["content"]
        assert "[" in system_message["content"]

    def test_system_prompt_specifies_category_to_files_mapping(self, prompt_builder, sample_file_data_single):
        """System prompt should clarify category -> files mapping format."""
        result = prompt_builder.build_prompt(sample_file_data_single, "Classify")
        system_message = next(msg for msg in result if msg["role"] == "system")
        # Should indicate the structure somehow (category name as key, file list as value)
        content_lower = system_message["content"].lower()
        assert "category" in content_lower or "類別" in system_message["content"]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_instruction(self, prompt_builder, sample_file_data_single):
        """Should handle empty instruction string."""
        result = prompt_builder.build_prompt(sample_file_data_single, "")
        assert result is not None

    def test_very_long_instruction(self, prompt_builder, sample_file_data_single):
        """Should handle very long instruction text."""
        long_instruction = "Classify files " * 100
        result = prompt_builder.build_prompt(sample_file_data_single, long_instruction)
        assert result is not None

    def test_special_characters_in_instruction(self, prompt_builder, sample_file_data_single):
        """Should handle special characters in instruction."""
        instruction = "Classify files with <special> & 'characters' \"quoted\""
        result = prompt_builder.build_prompt(sample_file_data_single, instruction)
        assert result is not None

    def test_unicode_emoji_in_data(self, prompt_builder):
        """Should handle Unicode emoji in file data."""
        emoji_json = json.dumps({"file📄.txt": {"path": "/path/file📄.txt", "content": "Hello 👋 World 🌍"}})
        result = prompt_builder.build_prompt(emoji_json, "Classify")
        assert result is not None
