"""
Pytest configuration and fixtures for LLM classifier tests.
"""

import pytest

from fileorg.llm_classifier.application.text_validator import BasicTextValidator


@pytest.fixture
def text_validator():
    """Provide a BasicTextValidator instance with default configuration."""
    return BasicTextValidator(max_length=150000)


@pytest.fixture
def custom_validator():
    """Provide a BasicTextValidator with custom max_length for testing."""
    return BasicTextValidator(max_length=100)


# Test data fixtures
@pytest.fixture
def valid_text_samples():
    """Provide valid text samples for testing."""
    return [
        "This is a simple text.",
        "Multi-line\ntext\nwith\nnewlines",
        "Text with    multiple   spaces",
        "Special characters: @#$%^&*()",
        "中文文字測試",
        "Mixed 中英文 text",
    ]


@pytest.fixture
def invalid_text_samples():
    """Provide invalid text samples for testing."""
    return [
        "",  # Empty string
        "   ",  # Only whitespace
        "  \n\n\t  ",  # Only whitespace with newlines
    ]


@pytest.fixture
def text_with_control_chars():
    """Provide text with control characters for sanitization testing."""
    return [
        "Text\x00with\x01null\x02chars",
        "Text\x08with\x0bbackspace",
        "Normal\x7ftext",
    ]


@pytest.fixture
def text_with_various_whitespace():
    """Provide text with various whitespace patterns."""
    return [
        "  Leading spaces",
        "Trailing spaces  ",
        "  Both sides  ",
        "Multiple    spaces    between",
        "Windows\r\nline\r\nendings",
        "Old Mac\rline\rendings",
        "Mixed\r\nline\nendings\rhere",
        "\n\nLeading newlines",
        "Trailing newlines\n\n",
    ]
