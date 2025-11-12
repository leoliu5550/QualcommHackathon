"""
Text validation adapter implementation.
"""

import re
from pathlib import Path
from typing import Dict

from fileorg.llm_classifier.ports.interfaces import ITextValidator


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

    def validate_path(self, path: str) -> bool:
        """
        Validate file path format.

        Checks:
        - Path is non-empty
        - Path appears to be absolute
        - Filename is extractable

        Args:
            path: File path to validate

        Returns:
            True if path format is valid, False otherwise
        """
        if not path or not path.strip():
            return False

        # Check if path looks like an absolute path
        # Support Windows (C:/), Unix (/), and common mount points
        path_stripped = path.strip()
        is_absolute = any(
            [
                path_stripped.startswith("C:/"),
                path_stripped.startswith("C:\\"),
                path_stripped.startswith("/"),
                path_stripped.startswith("/mnt/"),
                path_stripped.startswith("/Users/"),
                path_stripped.startswith("/home/"),
            ]
        )

        if not is_absolute:
            return False

        # Reject paths ending with separator (directory-only paths)
        if path_stripped.endswith("/") or path_stripped.endswith("\\"):
            return False

        # Check that we can extract a filename
        try:
            filename = Path(path).name
            if not filename or not filename.strip():
                return False
        except Exception:
            return False

        return True

    def validate_paths_dict(self, data: Dict[str, str]) -> bool:
        """
        Validate dictionary of file paths to content.

        Checks:
        - Dictionary is non-empty
        - All keys are valid paths
        - All values are valid text content

        Args:
            data: Dictionary mapping file paths to content strings

        Returns:
            True if all paths and content are valid, False otherwise
        """
        if not data or not isinstance(data, dict):
            return False

        if len(data) == 0:
            return False

        for path, content in data.items():
            # Validate path format
            if not self.validate_path(path):
                return False

            # Validate content (allow empty content for some files)
            if not isinstance(content, str):
                return False

        return True
