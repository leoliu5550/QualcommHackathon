"""
Unit tests for BasicTextValidator adapter.
"""

from fileorg.llm_classifier.adapters.text_validator import BasicTextValidator
from fileorg.llm_classifier.ports import ITextValidator


class TestBasicTextValidatorInterface:
    """Test that BasicTextValidator correctly implements ITextValidator interface."""

    def test_implements_interface(self, text_validator):
        """Verify BasicTextValidator implements ITextValidator."""
        assert isinstance(text_validator, ITextValidator)

    def test_has_sanitize_method(self, text_validator):
        """Verify sanitize method exists and is callable."""
        assert hasattr(text_validator, "sanitize")
        assert callable(text_validator.sanitize)

    def test_has_validate_method(self, text_validator):
        """Verify validate method exists and is callable."""
        assert hasattr(text_validator, "validate")
        assert callable(text_validator.validate)


class TestSanitizeMethod:
    """Test sanitize() method behavior."""

    def test_sanitize_empty_string(self, text_validator):
        """Empty string should return empty string."""
        result = text_validator.sanitize("")
        assert result == ""

    def test_sanitize_removes_leading_trailing_spaces(self, text_validator):
        """Leading and trailing spaces should be removed."""
        result = text_validator.sanitize("  AI Filing  ")
        assert result == "AI Filing"

    def test_sanitize_normalizes_multiple_spaces(self, text_validator):
        """Multiple consecutive spaces should become single space."""
        result = text_validator.sanitize("AI    Filing")
        assert result == "AI Filing"

    def test_sanitize_normalizes_line_endings_windows(self, text_validator):
        """Windows line endings (\r\n) should be normalized to \n."""
        result = text_validator.sanitize("line1\r\nline2\r\nline3")
        assert result == "line1\nline2\nline3"

    def test_sanitize_normalizes_line_endings_old_mac(self, text_validator):
        """Old Mac line endings (\r) should be normalized to \n."""
        result = text_validator.sanitize("line1\rline2\rline3")
        assert result == "line1\nline2\nline3"

    def test_sanitize_mixed_line_endings(self, text_validator):
        """Mixed line endings should all be normalized to \n."""
        result = text_validator.sanitize("line1\r\nline2\nline3\rline4")
        assert result == "line1\nline2\nline3\nline4"

    def test_sanitize_removes_control_characters(self, text_validator):
        """Control characters should be removed."""
        result = text_validator.sanitize("AI\x00\x01Filing\x02")
        assert result == "AIFiling"
        assert "\x00" not in result
        assert "\x01" not in result

    def test_sanitize_preserves_newlines(self, text_validator):
        """Newlines should be preserved after normalization."""
        result = text_validator.sanitize("line1\nline2\nline3")
        assert result == "line1\nline2\nline3"

    def test_sanitize_removes_leading_empty_lines(self, text_validator):
        """Leading empty lines should be removed."""
        result = text_validator.sanitize("\n\n\nAI")
        assert result == "AI"

    def test_sanitize_removes_trailing_empty_lines(self, text_validator):
        """Trailing empty lines should be removed."""
        result = text_validator.sanitize("AI\n\n\n")
        assert result == "AI"

    def test_sanitize_preserves_internal_empty_lines(self, text_validator):
        """Internal empty lines should be preserved."""
        result = text_validator.sanitize("line1\n\nline2")
        assert result == "line1\n\nline2"

    def test_sanitize_complex_whitespace(self, text_validator):
        """Complex whitespace patterns should be normalized."""
        input_text = "  \n\n  AI  \t  Filing  \n\n  "
        result = text_validator.sanitize(input_text)
        assert result == "AI Filing"

    def test_sanitize_preserves_unicode(self, text_validator):
        """Unicode characters should be preserved."""
        result = text_validator.sanitize("  檔案智能整理  ")
        assert result == "檔案智能整理"

    def test_sanitize_preserves_special_chars(self, text_validator):
        """Special characters should be preserved."""
        result = text_validator.sanitize("Price: $100.50 (20% off!)")
        assert result == "Price: $100.50 (20% off!)"


class TestValidateMethod:
    """Test validate() method behavior."""

    def test_validate_empty_string_returns_false(self, text_validator):
        """Empty string should be invalid."""
        assert text_validator.validate("") is False

    def test_validate_whitespace_only_returns_false(self, text_validator):
        """String with only whitespace should be invalid."""
        assert text_validator.validate("   ") is False
        assert text_validator.validate("\n\n\n") is False
        assert text_validator.validate("\t\t\t") is False
        assert text_validator.validate("  \n\t  ") is False

    def test_validate_valid_text_returns_true(self, text_validator):
        """Valid text should return True."""
        assert text_validator.validate("AI Filing") is True
        assert text_validator.validate("A") is True
        assert text_validator.validate("Multi\nline\ntext") is True

    def test_validate_respects_max_length(self, custom_validator):
        """Text exceeding max_length should be invalid."""
        # custom_validator has max_length=100
        short_text = "x" * 100
        long_text = "x" * 101

        assert custom_validator.validate(short_text) is True
        assert custom_validator.validate(long_text) is False

    def test_validate_default_max_length(self, text_validator):
        """Default max_length should be 150000."""
        # text_validator has max_length=150000
        assert text_validator.max_length == 150000

        text_at_limit = "x" * 150000
        text_over_limit = "x" * 150001

        assert text_validator.validate(text_at_limit) is True
        assert text_validator.validate(text_over_limit) is False

    def test_validate_unicode_text(self, text_validator):
        """Unicode text should be valid."""
        assert text_validator.validate("檔案智能整理") is True
        assert text_validator.validate("AI 整理") is True

    def test_validate_text_with_special_chars(self, text_validator):
        """Text with special characters should be valid."""
        assert text_validator.validate("$100.50") is True
        assert text_validator.validate("user@example.com") is True
        assert text_validator.validate("C:\\path\\to\\file") is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_sanitize_with_only_control_chars(self, text_validator):
        """String with only control characters should become empty."""
        result = text_validator.sanitize("\x00\x01\x02")
        assert result == ""

    def test_validate_single_character(self, text_validator):
        """Single character should be valid."""
        assert text_validator.validate("A") is True
        assert text_validator.validate("1") is True
        assert text_validator.validate("?") is True

    def test_sanitize_tabs_converted_to_spaces(self, text_validator):
        """Tabs should be treated as whitespace and normalized."""
        result = text_validator.sanitize("AI\t\tFiling")
        assert result == "AI Filing"

    def test_sanitize_mixed_content(self, text_validator):
        """Complex mixed content should be properly sanitized."""
        input_text = "\n\n  AI\r\n\tFiling  \x00  \n  Test  \n\n"
        result = text_validator.sanitize(input_text)
        # \r\n becomes \n, tab after newline is removed, control chars removed
        assert result == "AI\nFiling\nTest"

    def test_validator_with_zero_max_length(self):
        """Validator with zero max_length should reject all text."""
        validator = BasicTextValidator(max_length=0)
        assert validator.validate("any text") is False
        assert validator.validate("x") is False

    def test_validator_with_negative_max_length(self):
        """Validator with negative max_length should reject all text."""
        validator = BasicTextValidator(max_length=-1)
        assert validator.validate("any text") is False
