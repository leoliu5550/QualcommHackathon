"""
Unit tests for SummaryPromptBuilder.
"""

import json

import pytest

from fileorg.llm_classifier.adapters.prompt_builders import SummaryPromptBuilder
from fileorg.llm_classifier.adapters.template_loader import Jinja2TemplateLoader


@pytest.fixture
def template_loader():
    """Create template loader for v1 summary templates."""
    # Use default base_path which points to prompts/ directory
    return Jinja2TemplateLoader()


@pytest.fixture
def builder(template_loader):
    """Create SummaryPromptBuilder instance."""
    return SummaryPromptBuilder(
        template_loader=template_loader,
        provider="llama3b",
        version="v1",
    )


class TestSummaryPromptBuilder:
    """Test suite for SummaryPromptBuilder."""

    def test_initialization(self, template_loader):
        """Test successful initialization."""
        builder = SummaryPromptBuilder(
            template_loader=template_loader,
            provider="llama3b",
            version="v1",
        )
        assert builder.provider == "llama3b"
        assert builder.version == "v1"

    def test_initialization_missing_templates(self, template_loader):
        """Test initialization fails with missing templates."""
        with pytest.raises(FileNotFoundError, match="Summary system template not found"):
            SummaryPromptBuilder(
                template_loader=template_loader,
                provider="nonexistent",
                version="v999",
            )

    def test_build_prompt_success(self, builder):
        """Test successful prompt building."""
        file_data = {"C:/test.pdf": "This is a test file content"}
        text = json.dumps(file_data)
        instruction = "Extract keyword"

        messages = builder.build_prompt(text=text, instruction=instruction)

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert "<|begin_of_text|>" in messages[0]["content"]
        assert "<|start_header_id|>system<|end_header_id|>" in messages[0]["content"]
        assert "<|start_header_id|>user<|end_header_id|>" in messages[0]["content"]
        assert instruction in messages[0]["content"]

    def test_build_prompt_invalid_json(self, builder):
        """Test prompt building fails with invalid JSON."""
        invalid_text = "not a json string"

        with pytest.raises(ValueError, match="Input text must be valid JSON format"):
            builder.build_prompt(text=invalid_text, instruction="Extract keyword")

    def test_truncate_text(self, builder):
        """Test text truncation."""
        file_data = {"C:/test.pdf": "A" * 10000}
        text = json.dumps(file_data)
        max_tokens = 100  # Very small limit

        messages = builder.build_prompt(text=text, instruction="Test", max_tokens=max_tokens)

        # Should succeed and content should be truncated
        assert len(messages) == 1
        assert len(messages[0]["content"]) < len(text)

    def test_llama_chat_format(self, builder):
        """Test Llama chat format structure."""
        file_data = {"C:/test.pdf": "content"}
        text = json.dumps(file_data)

        messages = builder.build_prompt(text=text, instruction="Test")
        content = messages[0]["content"]

        # Verify Llama format tokens
        assert content.startswith("<|begin_of_text|>")
        assert "<|start_header_id|>system<|end_header_id|>" in content
        assert "<|eot_id|>" in content
        assert "<|start_header_id|>assistant<|end_header_id|>" in content
