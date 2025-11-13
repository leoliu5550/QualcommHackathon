"""
JSON output parser for LLM classification results.

This module provides a parser that extracts and validates JSON output from LLM responses,
handling common cases like markdown code blocks and explanatory text.
"""

from typing import Dict, List

from fileorg.llm_classifier.infrastructure import extract_json_from_llm_output
from fileorg.llm_classifier.ports.interfaces import IOutputParser


class JSONOutputParser(IOutputParser):
    """
    Parse JSON output from LLM responses, handling various formats.

    This parser is designed to handle real-world LLM outputs which may include:
    - Pure JSON responses
    - JSON wrapped in markdown code blocks (```json ... ```)
    - JSON with explanatory text before/after
    - Multiple JSON blocks (uses the first valid one)

    Example Inputs:
        1. Pure JSON:
           {"Documents": ["file1.txt"], "Code": ["app.py"]}

        2. Markdown wrapped:
           Here are the categories:
           ```json
           {"Documents": ["file1.txt"]}
           ```

        3. Mixed text:
           Based on analysis, I categorized as:
           {"Documents": ["file1.txt"]}
           Hope this helps!

    SOLID Principles:
        - Single Responsibility: Only parses JSON from text
        - Open/Closed: Can be extended via inheritance
        - Liskov Substitution: Fully implements IOutputParser
        - Interface Segregation: Implements only required methods
        - Dependency Inversion: Depends on IOutputParser abstraction
    """

    def __init__(self, strict: bool = False):
        """
        Initialize JSON output parser.

        Args:
            strict: If True, raise ValueError on any parsing issues.
                   If False, attempt to extract JSON from mixed content.
        """
        self.strict = strict

    def parse(self, text: str) -> Dict[str, List[str]]:
        """
        Parse LLM output to {category: [files]} format.

        Uses shared extract_json_from_llm_output() utility for JSON extraction.

        Args:
            text: Raw LLM text output

        Returns:
            Dict mapping category names to file lists

        Raises:
            ValueError: If no valid JSON found or format is incorrect
        """
        # Extract and parse JSON using shared utility
        data = extract_json_from_llm_output(text, strict=self.strict)

        # Validate structure
        self._validate_structure(data)

        return data

    def _validate_structure(self, data: dict) -> None:
        """
        Validate that parsed JSON has correct structure.

        Expected structure:
            {
                "Category1": ["file1.txt", "file2.pdf"],
                "Category2": ["file3.docx"]
            }

        Args:
            data: Parsed JSON data

        Raises:
            ValueError: If structure is invalid
        """
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object (dict), got {type(data).__name__}")

        if not data:
            raise ValueError("Output JSON cannot be empty")

        for category, files in data.items():
            # Validate category name
            if not isinstance(category, str):
                raise ValueError(f"Category name must be string, got {type(category).__name__}")

            if not category.strip():
                raise ValueError("Category name cannot be empty")

            # Validate file list
            if not isinstance(files, list):
                raise ValueError(f"File list for category '{category}' must be array, got {type(files).__name__}")

            # Validate each filename
            for idx, filename in enumerate(files):
                if not isinstance(filename, str):
                    raise ValueError(f"File name at index {idx} in category '{category}' must be string, got {type(filename).__name__}")
