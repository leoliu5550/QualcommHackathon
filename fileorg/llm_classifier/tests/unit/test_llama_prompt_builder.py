"""
Unit tests for LlamaPromptBuilder adapter.

Tests verify that LlamaPromptBuilder correctly implements the IPromptBuilder
interface and produces valid Llama 3 chat-formatted prompts using Jinja2 templates.
"""

import json

import pytest

from fileorg.llm_classifier.adapters.template_loader import Jinja2TemplateLoader
from fileorg.llm_classifier.application.llama_prompt_builder import LlamaPromptBuilder
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
            "analysis.pdf": {"path": "/stats/analysis.pdf", "content": "Statistical analysis of customer data"},
            "meeting_notes.docx": {"path": "/docs/meeting_notes.docx", "content": "Meeting notes from team sync"},
            "data.csv": {"path": "/data/data.csv", "content": "timestamp,value,category\n2024-01-01,100,A\n"},
        }
    )


@pytest.fixture
def template_loader():
    """Provide a template loader with real template files."""
    # Use actual template files from prompts/ directory
    return Jinja2TemplateLoader()


@pytest.fixture
def llama3b_builder(template_loader):
    """Provide a Llama 3B prompt builder."""
    return LlamaPromptBuilder(template_loader=template_loader, provider="llama3b", version="v1")


@pytest.fixture
def llama8b_builder(template_loader):
    """Provide a Llama 8B prompt builder."""
    return LlamaPromptBuilder(template_loader=template_loader, provider="llama8b", version="v1")


class TestLlamaPromptBuilderInterface:
    """Test that LlamaPromptBuilder correctly implements IPromptBuilder interface."""

    def test_implements_interface(self, llama3b_builder):
        """Verify LlamaPromptBuilder implements IPromptBuilder."""
        assert isinstance(llama3b_builder, IPromptBuilder)

    def test_has_build_prompt_method(self, llama3b_builder):
        """Verify build_prompt method exists and is callable."""
        assert hasattr(llama3b_builder, "build_prompt")
        assert callable(llama3b_builder.build_prompt)


class TestInitialization:
    """Test builder initialization and configuration."""

    def test_initialization_with_valid_templates(self, template_loader):
        """Should initialize successfully with valid provider/version."""
        builder = LlamaPromptBuilder(template_loader=template_loader, provider="llama3b", version="v1")
        assert builder.provider == "llama3b"
        assert builder.version == "v1"

    def test_initialization_with_nonexistent_provider(self, template_loader):
        """Should raise FileNotFoundError for nonexistent provider."""
        with pytest.raises(FileNotFoundError, match="System template not found"):
            LlamaPromptBuilder(template_loader=template_loader, provider="nonexistent", version="v1")

    def test_initialization_with_suggested_categories(self, template_loader):
        """Should store suggested categories."""
        categories = ["Documents", "Code", "Data"]
        builder = LlamaPromptBuilder(template_loader=template_loader, provider="llama3b", version="v1", suggested_categories=categories)
        assert builder.suggested_categories == categories


class TestBuildPromptMethod:
    """Test build_prompt() method behavior and output format."""

    def test_returns_list_of_dicts(self, llama3b_builder, sample_file_data_single):
        """Should return a list of message dictionaries."""
        result = llama3b_builder.build_prompt(sample_file_data_single, "Classify these files")
        assert isinstance(result, list)
        assert len(result) == 1  # Llama format uses single message
        assert isinstance(result[0], dict)

    def test_message_has_required_keys(self, llama3b_builder, sample_file_data_single):
        """Message should have 'role' and 'content' keys."""
        result = llama3b_builder.build_prompt(sample_file_data_single, "Classify these files")
        msg = result[0]
        assert "role" in msg
        assert "content" in msg
        assert msg["role"] == "user"
        assert isinstance(msg["content"], str)

    def test_content_contains_llama_special_tokens(self, llama3b_builder, sample_file_data_single):
        """Content should contain Llama 3 special tokens."""
        result = llama3b_builder.build_prompt(sample_file_data_single, "Classify these files")
        content = result[0]["content"]

        # Check for Llama 3 special tokens
        assert "<|begin_of_text|>" in content
        assert "<|start_header_id|>system<|end_header_id|>" in content
        assert "<|start_header_id|>user<|end_header_id|>" in content
        assert "<|start_header_id|>assistant<|end_header_id|>" in content
        assert "<|eot_id|>" in content

    def test_content_contains_instruction(self, llama3b_builder, sample_file_data_single):
        """Content should contain the provided instruction."""
        instruction = "Organize files by category"
        result = llama3b_builder.build_prompt(sample_file_data_single, instruction)
        content = result[0]["content"]
        assert instruction in content

    def test_content_contains_file_data(self, llama3b_builder, sample_file_data_batch):
        """Content should contain file data."""
        result = llama3b_builder.build_prompt(sample_file_data_batch, "Classify files")
        content = result[0]["content"]
        assert "analysis.pdf" in content


class TestJSONInputHandling:
    """Test handling of JSON-formatted file data."""

    def test_accepts_valid_json_string(self, llama3b_builder, sample_file_data_single):
        """Should accept valid JSON string without errors."""
        result = llama3b_builder.build_prompt(sample_file_data_single, "Classify")
        assert result is not None

    def test_rejects_invalid_json(self, llama3b_builder):
        """Should raise ValueError for invalid JSON input."""
        invalid_json = "This is not JSON {invalid"
        with pytest.raises(ValueError, match="valid JSON format"):
            llama3b_builder.build_prompt(invalid_json, "Classify")

    def test_handles_empty_json_object(self, llama3b_builder):
        """Should handle empty JSON object."""
        empty_json = json.dumps({})
        result = llama3b_builder.build_prompt(empty_json, "Classify")
        assert result is not None


class TestProviderSpecificBehavior:
    """Test behavior specific to different providers (llama3b vs llama8b)."""

    def test_llama3b_and_llama8b_produce_different_content(self, llama3b_builder, llama8b_builder, sample_file_data_single):
        """Different providers should produce different prompts."""
        result_3b = llama3b_builder.build_prompt(sample_file_data_single, "Classify")
        result_8b = llama8b_builder.build_prompt(sample_file_data_single, "Classify")

        content_3b = result_3b[0]["content"]
        content_8b = result_8b[0]["content"]

        # System prompts should be different (8B has "enhanced reasoning")
        assert content_3b != content_8b

    def test_llama8b_contains_enhanced_prompt(self, llama8b_builder, sample_file_data_single):
        """Llama 8B should contain enhanced reasoning prompt."""
        result = llama8b_builder.build_prompt(sample_file_data_single, "Classify")
        content = result[0]["content"]

        # Check for enhanced prompt characteristics (based on template)
        assert "enhanced" in content.lower() or "reasoning" in content.lower()


class TestSuggestedCategories:
    """Test handling of suggested categories."""

    def test_prompt_includes_suggested_categories(self, template_loader, sample_file_data_single):
        """Prompt should include suggested categories when provided."""
        categories = ["Documents", "Statistics", "Media"]
        builder = LlamaPromptBuilder(template_loader=template_loader, provider="llama3b", version="v1", suggested_categories=categories)

        result = builder.build_prompt(sample_file_data_single, "Classify")
        content = result[0]["content"]

        # Should contain at least some of the categories
        assert any(cat in content for cat in categories)

    def test_prompt_without_suggested_categories(self, llama3b_builder, sample_file_data_single):
        """Prompt should work without suggested categories."""
        result = llama3b_builder.build_prompt(sample_file_data_single, "Classify")
        content = result[0]["content"]

        # Should mention dynamic category creation
        assert "dynamic" in content.lower() or "dynamically" in content.lower()


class TestTokenLimitHandling:
    """Test token limit and text truncation behavior."""

    def test_respects_max_tokens_parameter(self, llama3b_builder):
        """Should truncate text when it exceeds max_tokens."""
        large_content = "A" * 100000
        large_json = json.dumps({"large_file.txt": {"path": "/path", "content": large_content}})

        max_tokens = 1000
        result = llama3b_builder.build_prompt(large_json, "Classify", max_tokens=max_tokens)

        # Result should be generated without errors
        assert result is not None
        content = result[0]["content"]
        # Content shouldn't be excessively long (rough check)
        assert len(content) < max_tokens * 5  # Allow overhead for templates

    def test_handles_small_max_tokens(self, llama3b_builder, sample_file_data_single):
        """Should handle very small max_tokens values."""
        result = llama3b_builder.build_prompt(sample_file_data_single, "Classify", max_tokens=10)
        assert result is not None


class TestLlamaFormatStructure:
    """Test that the Llama 3 chat format is correctly structured."""

    def test_format_begins_with_begin_of_text(self, llama3b_builder, sample_file_data_single):
        """Format should begin with <|begin_of_text|>."""
        result = llama3b_builder.build_prompt(sample_file_data_single, "Classify")
        content = result[0]["content"]
        assert content.startswith("<|begin_of_text|>")

    def test_format_has_correct_message_order(self, llama3b_builder, sample_file_data_single):
        """Format should have messages in correct order: system, user, assistant."""
        result = llama3b_builder.build_prompt(sample_file_data_single, "Classify")
        content = result[0]["content"]

        # Find positions of role headers
        system_pos = content.find("<|start_header_id|>system<|end_header_id|>")
        user_pos = content.find("<|start_header_id|>user<|end_header_id|>")
        assistant_pos = content.find("<|start_header_id|>assistant<|end_header_id|>")

        # Verify order
        assert system_pos < user_pos < assistant_pos

    def test_format_ends_with_assistant_header(self, llama3b_builder, sample_file_data_single):
        """Format should end with assistant header to prompt generation."""
        result = llama3b_builder.build_prompt(sample_file_data_single, "Classify")
        content = result[0]["content"]
        assert content.rstrip().endswith("<|start_header_id|>assistant<|end_header_id|>")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_instruction(self, llama3b_builder, sample_file_data_single):
        """Should handle empty instruction string."""
        result = llama3b_builder.build_prompt(sample_file_data_single, "")
        assert result is not None

    def test_very_long_instruction(self, llama3b_builder, sample_file_data_single):
        """Should handle very long instruction text."""
        long_instruction = "Classify files " * 100
        result = llama3b_builder.build_prompt(sample_file_data_single, long_instruction)
        assert result is not None

    def test_special_characters_in_instruction(self, llama3b_builder, sample_file_data_single):
        """Should handle special characters in instruction."""
        instruction = "Classify files with <special> & 'characters' \"quoted\""
        result = llama3b_builder.build_prompt(sample_file_data_single, instruction)
        assert result is not None
        # Instruction should be preserved in output
        assert instruction in result[0]["content"]
