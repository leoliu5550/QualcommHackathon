"""
Infrastructure layer for LLM classifier.

This layer contains shared technical utilities and infrastructure concerns
that don't implement domain interfaces but are used across the application.

Contents:
- json_extraction: Utilities for extracting JSON from LLM outputs
- factories: Factory classes for creating instances
"""

from .json_extraction import extract_json_from_llm_output

__all__ = ["extract_json_from_llm_output"]
