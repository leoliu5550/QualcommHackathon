"""
Text validation adapter implementation.
"""

import re

from fileorg.llm_classifier.ports import ITextValidator


class BasicTextValidator(ITextValidator):
    """
    Basic text validator for sanitizing and validating text inputs.

    Provides text cleaning and validation suitable for LLM inputs and outputs.
    """

    def __init__(self, max_length: int = 150000):
        """
        Initialize validator.

        Args:
            max_length: Maximum allowed text length in characters.
        """
        self.max_length = max_length

    def sanitize(self, text: str) -> str:
        """
        Sanitize text by removing control characters and normalizing whitespace.

        Args:
            text: Raw text to sanitize.

        Returns:
            Cleaned text with normalized whitespace and no control characters.
        """
        if not text:
            return ""

        # Normalize line endings to \n
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove control characters except newlines and tabs
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)

        # Replace multiple spaces with single space (but preserve newlines)
        text = re.sub(r"[ \t]+", " ", text)

        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]

        # Remove empty lines from start and end, but preserve internal empty lines
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()

        return "\n".join(lines)

    def validate(self, text: str) -> bool:
        """
        Check if text is valid for processing.

        Args:
            text: Text to validate.

        Returns:
            True if text is non-empty and within length limits, False otherwise.
        """
        if not text:
            return False

        # Check if text is only whitespace
        if not text.strip():
            return False

        # Check length constraint
        if len(text) > self.max_length:
            return False

        return True
