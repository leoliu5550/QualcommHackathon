"""
Summary Output Parser Implementation for Stage 1.

Parses LLM output from keyword extraction and creates FileSummary objects.
"""

from typing import Optional

from loguru import logger

from fileorg.llm_classifier.infrastructure import extract_json_from_llm_output
from fileorg.llm_classifier.ports.interfaces import ISummaryParser
from fileorg.llm_classifier.ports.models import FileSummary


class SummaryOutputParser(ISummaryParser):
    """
    Parse LLM output from Stage 1 keyword extraction.

    Responsibilities:
    1. Extract JSON from LLM response (handle markdown code blocks)
    2. Validate keyword format (1-2 words)
    3. Create FileSummary objects for each file

    Usage:
        parser = SummaryOutputParser()
        summary = parser.parse(llm_response, file_path="/path/to/file.txt")
        # Returns: FileSummary(file_path="...", summary="keyword", ...)
    """

    def parse(
        self,
        text: str,
        file_path: Optional[str] = None,
        raw_length: Optional[int] = None,
    ) -> FileSummary:
        """
        Parse LLM output to FileSummary object.

        Args:
            text: Raw LLM text output containing JSON with keywords
            file_path: Expected file path for validation
            raw_length: Optional length of raw response for metadata

        Returns:
            FileSummary object containing file path and keyword

        Raises:
            ValueError: If parsing fails or keyword format is invalid
        """
        try:
            # Step 1: Extract JSON from response using shared utility
            json_data = extract_json_from_llm_output(text, strict=False)

            # Step 2: Extract keyword for the specified file_path
            if file_path and file_path not in json_data:
                raise ValueError(f"File path '{file_path}' not found in LLM output")

            # Get the first file path if not specified
            target_path = file_path if file_path else list(json_data.keys())[0]
            keyword = json_data[target_path]

            # Step 3: Validate keyword format
            self._validate_keyword(keyword, target_path)

            # Step 4: Create FileSummary object
            metadata = {
                "raw_length": raw_length if raw_length else len(text),
                "keyword_length": len(keyword.split()),
            }

            summary = FileSummary(
                file_path=target_path,
                summary=keyword.strip(),
                metadata=metadata,
            )

            # Use repr() to avoid UnicodeEncodeError on Windows console
            logger.debug(f"Successfully parsed keyword for {target_path}: {repr(keyword)}")
            return summary

        except ValueError as e:
            logger.error(f"Summary parsing failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Summary parsing failed: {e}")
            raise ValueError(f"Failed to parse LLM summary output: {e}") from e

    def _validate_keyword(self, keyword: str, file_path: str) -> None:
        """
        Validate that keyword is in correct format (1-2 words).

        Args:
            keyword: Extracted keyword string
            file_path: File path (for error messages)

        Raises:
            ValueError: If keyword format is invalid
        """
        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError(f"Invalid keyword for {file_path}: must be non-empty string")

        word_count = len(keyword.strip().split())
        if word_count > 3:  # Allow up to 3 words for flexibility
            logger.warning(f"Keyword for {file_path} has {word_count} words (expected 1-2): '{keyword}'")
