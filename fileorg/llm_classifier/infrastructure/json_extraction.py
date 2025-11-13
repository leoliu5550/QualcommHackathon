"""
JSON extraction utilities for LLM output processing.

This module provides shared infrastructure utilities used by multiple adapters
within the LLM classifier. It contains technical implementations for parsing
LLM responses, which is an infrastructure concern.
"""

import json
import re
from typing import Any, Dict


def extract_json_from_llm_output(text: str, strict: bool = False) -> Dict[str, Any]:
    """
    Extract and parse JSON from LLM output text.

    This is a shared infrastructure utility used by output parsers to handle
    the technical complexity of extracting JSON from various LLM response formats.

    Handles various LLM output formats:
    - Pure JSON responses: {"key": "value"}
    - JSON wrapped in markdown code blocks: ```json ... ```
    - JSON with explanatory text before/after
    - Multiple JSON blocks (uses the first valid one)

    Args:
        text: Raw LLM output text that may contain JSON
        strict: If True, raise ValueError on any parsing issues.
               If False, attempt to extract JSON from mixed content.

    Returns:
        Parsed JSON as a dictionary

    Raises:
        ValueError: If no valid JSON found or parsing fails

    Examples:
        >>> # Pure JSON
        >>> extract_json_from_llm_output('{"category": "Documents"}')
        {'category': 'Documents'}

        >>> # Markdown wrapped
        >>> extract_json_from_llm_output('```json\\n{"category": "Documents"}\\n```')
        {'category': 'Documents'}

        >>> # With explanatory text
        >>> extract_json_from_llm_output('Here is the result:\\n{"category": "Documents"}')
        {'category': 'Documents'}
    """
    if not text or not text.strip():
        raise ValueError("Output text cannot be empty")

    # Extract JSON string using multiple strategies
    json_str = _extract_json_string(text, strict)

    # Parse the extracted JSON
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object (dict), got {type(data).__name__}")
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}") from e


def _extract_json_string(text: str, strict: bool = False) -> str:
    """
    Extract JSON string from text using multiple strategies.

    Extraction Strategy:
        1. Look for JSON in markdown code blocks (```json ... ``` or ``` ... ```)
        2. Look for JSON object patterns using regex
        3. Try to parse entire text as JSON
        4. (Non-strict) Last resort: Find content between first { and last }

    Args:
        text: Raw text potentially containing JSON
        strict: If True, fail immediately if strategies 1-3 don't work

    Returns:
        Extracted JSON string

    Raises:
        ValueError: If no valid JSON found
    """
    # Strategy 1: Look for JSON in markdown code blocks
    code_block_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL | re.IGNORECASE)
    code_block_match = code_block_pattern.search(text)

    if code_block_match:
        json_str = code_block_match.group(1).strip()
        if _is_valid_json(json_str):
            return json_str

    # Strategy 2: Look for JSON object patterns
    # This pattern handles nested objects (one level deep)
    json_object_pattern = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", re.DOTALL)
    json_matches = json_object_pattern.findall(text)

    for match in json_matches:
        if _is_valid_json(match):
            return match

    # Strategy 3: Try to parse entire text as JSON
    if _is_valid_json(text.strip()):
        return text.strip()

    # If strict mode, fail immediately
    if strict:
        raise ValueError("No valid JSON found in output")

    # Strategy 4: Last resort - Find content between first { and last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        potential_json = text[first_brace : last_brace + 1]
        if _is_valid_json(potential_json):
            return potential_json

    raise ValueError('Could not extract valid JSON from output. Expected format: {"key": "value"} or JSON in markdown code blocks')


def _is_valid_json(text: str) -> bool:
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
