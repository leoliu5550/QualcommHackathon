"""
Application Layer (Use Cases).

This layer contains use cases that orchestrate business logic.
Parsers and builders have been moved to the adapters layer.

FileClassifier now implements two-stage LLM processing for improved accuracy.
"""

from fileorg.llm_classifier.application.file_classifier import FileClassifier

__all__ = ["FileClassifier"]
