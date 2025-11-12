"""
LLM Classifier Ports - Interface Definitions

This module defines all interfaces and models following Hexagonal Architecture principles.
"""

from .interfaces import (
    IClassifierUseCase,
    ILLMProvider,
    IOutputParser,
    IPromptBuilder,
    ISummaryParser,
    ITemplateLoader,
    ITextValidator,
)
from .models import (
    ClassificationOutput,
    FileMapping,
    FileSummary,
    LLMInput,
)

__all__ = [
    # Models
    "LLMInput",
    "FileSummary",
    "ClassificationOutput",
    "FileMapping",
    # Interfaces
    "IClassifierUseCase",
    "ILLMProvider",
    "IPromptBuilder",
    "ISummaryParser",
    "IOutputParser",
    "ITextValidator",
    "ITemplateLoader",
]
