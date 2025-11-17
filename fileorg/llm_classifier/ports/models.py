"""
LLM Classifier Models - Data Classes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMInput:
    """
    Text input for LLM processing.

    Usage:
        input = LLMInput(text="content", max_tokens=150000)
        result = llm.classify(input)

    Args:
        text: Input text content
        max_tokens: Token limit (model-dependent, not business logic)
    """

    text: str
    max_tokens: int = 150000


@dataclass
class FileSummary:
    """
    Single file summary result from Stage 1.

    Represents the summarization output for a single file.
    Now supports file IDs to prevent path matching issues (e.g., double spaces).

    Usage:
        # New ID-based approach (recommended)
        summary = FileSummary(
            file_path="C:/Desktop/report.pdf",
            summary="Q4 financial report with earnings data",
            file_id="A001",
            metadata={"tokens": 150, "time_ms": 234}
        )

        # Legacy path-only approach (backward compatible)
        summary = FileSummary(
            file_path="C:/Desktop/report.pdf",
            summary="Q4 financial report",
            metadata={"tokens": 150}
        )

    Args:
        file_path: Absolute path of the file
        summary: Brief content summary (1-2 sentences)
        file_id: Optional stable file identifier (e.g., "A001")
                 Use this to avoid LLM path normalization issues
        metadata: Optional metadata (tokens, processing time, etc.)
    """

    file_path: str
    summary: str
    file_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ClassificationOutput:
    """
    File path mapping classification result.

    Maps files to organized paths with categorization metadata.

    Usage:
        output = ClassificationOutput(
            path_mappings={
                "C:/Desktop/report.pdf": FileMapping(
                    old_path="C:/Desktop/report.pdf",
                    new_relative_path="Financial_Reports/report.pdf",
                    category="Financial Reports",
                    summary="Q4 earnings report",
                    reason="Contains financial data"
                )
            },
            raw_responses={
                "stage1_summaries": "...",
                "stage2_classification": "..."
            }
        )

    Args:
        path_mappings: Dict mapping old paths to FileMapping objects
        raw_responses: Dict containing raw LLM outputs from both stages
                       Keys: "stage1_summaries", "stage2_classification"
        metadata: Optional metadata (token counts, file count, etc.)
    """

    path_mappings: Dict[str, "FileMapping"]
    raw_responses: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class FileMapping:
    """
    Single file path mapping with metadata.

    Maps an old absolute path to a new organized relative path with categorization info.
    Now supports file IDs for stable tracking through LLM processing.

    Usage:
        # New ID-based approach (recommended)
        mapping = FileMapping(
            old_path="C:/Desktop/report.pdf",
            new_relative_path="Financial_Reports/report.pdf",
            category="Financial Reports",
            summary="Q4 financial report",
            reason="Contains financial data",
            file_id="A001"
        )

        # Legacy path-only approach (backward compatible)
        mapping = FileMapping(
            old_path="C:/Desktop/report.pdf",
            new_relative_path="Financial_Reports/report.pdf",
            category="Financial Reports",
            summary="Q4 financial report",
            reason="Contains financial data"
        )

    Args:
        old_path: Original absolute file path
        new_relative_path: New organized relative path (Category_Name/filename)
        category: Original category name (spaces preserved)
        summary: Brief content summary (1-2 sentences)
        reason: Classification reasoning
        file_id: Optional stable file identifier (e.g., "A001")
                 Use this to track files through LLM processing stages
    """

    old_path: str
    new_relative_path: str
    category: str
    summary: str
    reason: str
    file_id: Optional[str] = None
