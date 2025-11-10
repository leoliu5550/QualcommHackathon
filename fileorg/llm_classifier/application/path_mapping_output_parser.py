"""
Path Mapping Output Parser Implementation.

Parses LLM output and assembles file path mappings.
"""

import json
import re
from pathlib import Path
from typing import Dict

from loguru import logger

from fileorg.llm_classifier.ports import FileMapping, IOutputParser


class PathMappingOutputParser(IOutputParser):
    """
    Parse LLM output and assemble path mappings.

    Responsibilities:
    1. Extract JSON from LLM response (handle markdown code blocks)
    2. Validate required fields (category, summary, reason)
    3. Path assembly logic:
       - Extract filename from old_path
       - Normalize category name (spaces → "_")
       - Combine to "Category_Name/filename"
    4. Create FileMapping objects

    Usage:
        parser = PathMappingOutputParser()
        mappings = parser.parse(llm_response)
        # Returns: Dict[str, FileMapping]
    """

    def parse(self, text: str) -> Dict[str, FileMapping]:
        """
        Parse LLM output to path mappings.

        Args:
            text: Raw LLM output text (may contain JSON in markdown)

        Returns:
            Dictionary mapping old paths to FileMapping objects

        Raises:
            ValueError: If parsing fails or required fields are missing
        """
        try:
            # Step 1: Extract JSON from response
            json_data = self._extract_json(text)

            # Step 2: Validate and assemble mappings
            mappings = {}
            for old_path, info in json_data.items():
                # Validate required fields
                self._validate_fields(info, old_path)

                # Path assembly logic (Single Responsibility)
                mapping = self._assemble_path_mapping(old_path, info)
                mappings[old_path] = mapping

            logger.info(f"Successfully parsed {len(mappings)} file mappings")
            return mappings

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Invalid JSON in LLM output: {e}") from e
        except Exception as e:
            logger.error(f"Path mapping parsing failed: {e}")
            raise ValueError(f"Failed to parse LLM output: {e}") from e

    def _extract_json(self, text: str) -> Dict:
        """
        Extract JSON from text, handling markdown code blocks.

        Supports:
        - Plain JSON: {"key": "value"}
        - Markdown: ```json\n{...}\n```
        - Markdown: ```\n{...}\n```

        Args:
            text: Raw text containing JSON

        Returns:
            Parsed JSON dictionary

        Raises:
            json.JSONDecodeError: If JSON is invalid
        """
        if not text or not text.strip():
            raise ValueError("Empty response from LLM")

        # Try to extract JSON from markdown code block
        # Pattern: ```json ... ``` or ``` ... ```
        code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
        matches = re.findall(code_block_pattern, text, re.DOTALL)

        if matches:
            # Use the first code block found
            json_text = matches[0].strip()
            logger.debug("Extracted JSON from markdown code block")
        else:
            # Try to find JSON object directly
            # Look for content between first { and last }
            json_pattern = r"\{.*\}"
            matches = re.findall(json_pattern, text, re.DOTALL)
            if matches:
                json_text = matches[0].strip()
                logger.debug("Extracted JSON from text")
            else:
                json_text = text.strip()

        # Parse JSON
        try:
            data = json.loads(json_text)
            if not isinstance(data, dict):
                raise ValueError("Expected JSON object, got other type")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}\nText: {json_text[:200]}...")
            raise

    def _validate_fields(self, info: Dict, old_path: str) -> None:
        """
        Validate that required fields exist in file info.

        Args:
            info: File information dictionary from LLM
            old_path: Original file path (for error messages)

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["category", "summary", "reason"]

        for field in required_fields:
            if field not in info:
                raise ValueError(f"Missing required field '{field}' for path: {old_path}")

            if not isinstance(info[field], str) or not info[field].strip():
                raise ValueError(f"Invalid '{field}' value for path: {old_path}")

    def _assemble_path_mapping(self, old_path: str, info: Dict) -> FileMapping:
        """
        Assemble file path mapping from LLM output.

        Path assembly logic:
        1. Extract filename from absolute path
        2. Normalize category name: "Category Name" → "Category_Name"
        3. Combine to: "Category_Name/filename"

        Args:
            old_path: Original absolute file path
            info: File information from LLM (category, summary, reason)

        Returns:
            FileMapping object with assembled path

        Raises:
            ValueError: If path assembly fails
        """
        try:
            # Extract filename from absolute path
            filename = Path(old_path).name
            if not filename:
                raise ValueError(f"Cannot extract filename from path: {old_path}")

            # Normalize category name (spaces → underscores)
            category = info["category"].strip()
            category_normalized = category.replace(" ", "_")

            # Assemble new relative path: "Category_Name/filename"
            new_relative_path = f"{category_normalized}/{filename}"

            # Create FileMapping object
            mapping = FileMapping(
                old_path=old_path,
                new_relative_path=new_relative_path,
                category=category,  # Preserve original category name
                summary=info["summary"].strip(),
                reason=info["reason"].strip(),
            )

            logger.debug(f"Assembled mapping: {old_path} → {new_relative_path}")
            return mapping

        except Exception as e:
            logger.error(f"Path assembly failed for {old_path}: {e}")
            raise ValueError(f"Failed to assemble path for {old_path}: {e}") from e
