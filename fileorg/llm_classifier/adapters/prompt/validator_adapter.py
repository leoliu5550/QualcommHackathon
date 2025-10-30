"""
Output Validator Adapter

This adapter implements OutputValidatorPort by wrapping the PromptOptimizer
validation and sanitization logic.

SOLID Principles:
    - Single Responsibility: Only handles output validation and sanitization
    - Liskov Substitution: Can replace any OutputValidatorPort implementation
    - Dependency Inversion: Implements the abstract OutputValidatorPort
"""

import re
from fileorg.llm_classifier.ports import OutputValidatorPort
from fileorg.llm_classifier.adapters.prompt._optimizer import PromptOptimizer


class OutputValidatorAdapter(OutputValidatorPort):
    """
    Adapter for validating and sanitizing LLM outputs.

    Provides validation for JSON outputs and folder name sanitization
    to ensure file system compatibility.

    Attributes:
        optimizer: PromptOptimizer instance for validation logic
    """

    def __init__(self):
        """Initialize output validator adapter."""
        self.optimizer = PromptOptimizer()

    def validate_json(self, text: str) -> tuple[bool, str]:
        """
        Validate and fix JSON output.

        Args:
            text: Raw text output from LLM

        Returns:
            Tuple of (is_valid, cleaned_text)
        """
        return self.optimizer.validate_output(text, "json")

    def sanitize_folder_name(self, name: str) -> str:
        """
        Sanitize folder name for file system compatibility.

        Removes unwanted characters while preserving Chinese characters,
        English letters, digits, spaces, and forward slashes.

        Args:
            name: Raw folder name

        Returns:
            Sanitized folder name safe for file systems
        """
        # Keep Chinese, English, digits, spaces, and forward slashes
        cleaned = re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9\s/]', '', name)

        # Remove the word "foldername" (case insensitive)
        cleaned = re.sub(r'foldername', '', cleaned, flags=re.IGNORECASE)

        return cleaned.strip()
