"""
Text validation adapter implementation.
"""

import re
from typing import Any, Optional

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

    def validate_path(self, path: Optional[str]) -> bool:
        """
        Validate that a path is an absolute path with a filename.

        Args:
            path: Path string to validate.

        Returns:
            True if path is a valid absolute path with a filename, False otherwise.
        """
        # Reject None, empty strings, or whitespace-only strings
        if path is None or not path or not path.strip():
            return False

        # Normalize path separators
        normalized_path = path.replace("\\", "/")

        # Check if it's an absolute path (Windows or Unix)
        # Windows: starts with drive letter (e.g., C:/)
        # Unix: starts with /
        is_windows_absolute = bool(re.match(r"^[A-Za-z]:/", normalized_path))
        is_unix_absolute = normalized_path.startswith("/")

        if not (is_windows_absolute or is_unix_absolute):
            return False

        # Reject if path ends with a slash (directory only, no filename)
        if normalized_path.endswith("/"):
            return False

        # Extract the filename (last component after final /)
        filename = normalized_path.split("/")[-1]

        # Ensure there's a filename present
        if not filename or filename.strip() == "":
            return False

        return True

    def validate_paths_dict(self, paths_dict: Any) -> bool:
        """
        Validate a dictionary of paths to content.

        Args:
            paths_dict: Dictionary with file paths as keys and content as values.

        Returns:
            True if dictionary is valid (non-empty, all paths valid, all values are strings),
            False otherwise.
        """
        # Reject None or non-dictionary types
        if paths_dict is None or not isinstance(paths_dict, dict):
            return False

        # Reject empty dictionaries
        if not paths_dict:
            return False

        # Validate each path and content
        for path, content in paths_dict.items():
            # Validate the path
            if not self.validate_path(path):
                return False

            # Validate that content is a string (can be empty)
            if not isinstance(content, str):
                return False

        return True
