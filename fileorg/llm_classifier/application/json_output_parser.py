"""
JSON output parser for LLM classification results.

This module provides a parser that extracts and validates JSON output from LLM responses,
handling common cases like markdown code blocks and explanatory text.
"""

import json
import re
from typing import Dict, List

from fileorg.llm_classifier.ports import IOutputParser


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

    # Regex patterns for extracting JSON
    # Pattern 1: JSON in markdown code blocks
    JSON_CODE_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)

    # Pattern 2: JSON object (simple heuristic)
    JSON_OBJECT_PATTERN = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", re.DOTALL)

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

        Extraction Strategy:
            1. Try to find JSON in markdown code blocks
            2. Try to find JSON object patterns
            3. Try to parse entire text as JSON

        Args:
            text: Raw LLM text output

        Returns:
            Dict mapping category names to file lists

        Raises:
            ValueError: If no valid JSON found or format is incorrect
        """
        if not text or not text.strip():
            raise ValueError("Output text cannot be empty")

        # Try extraction strategies in order
        json_str = self._extract_json(text)

        # Parse the extracted JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}") from e

        # Validate structure
        self._validate_structure(data)

        return data

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON string from text using multiple strategies.

        Args:
            text: Raw text potentially containing JSON

        Returns:
            Extracted JSON string

        Raises:
            ValueError: If no valid JSON found
        """
        # Strategy 1: Look for JSON in markdown code blocks
        code_block_match = self.JSON_CODE_BLOCK_PATTERN.search(text)
        if code_block_match:
            json_str = code_block_match.group(1).strip()
            if self._is_valid_json(json_str):
                return json_str

        # Strategy 2: Look for JSON object patterns
        json_matches = self.JSON_OBJECT_PATTERN.findall(text)
        for match in json_matches:
            if self._is_valid_json(match):
                return match

        # Strategy 3: Try to parse entire text as JSON
        if self._is_valid_json(text.strip()):
            return text.strip()

        # If strict mode, fail immediately
        if self.strict:
            raise ValueError("No valid JSON found in output")

        # Last resort: Try to find anything between first { and last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")

        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            potential_json = text[first_brace : last_brace + 1]
            if self._is_valid_json(potential_json):
                return potential_json

        raise ValueError('Could not extract valid JSON from output. Expected format: {"Category": ["file1.txt", "file2.txt"]}')

    def _is_valid_json(self, text: str) -> bool:
        """
        Check if text is valid JSON.

        Args:
            text: Text to validate

        Returns:
            True if valid JSON, False otherwise
        """
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

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
