"""
Prompt Engineering Module for FileOrg

This module provides advanced prompt templates and builders for improved file classification.
It's designed to be fully backward compatible with the existing system.
"""

from .templates import PromptTemplates
from .builder import PromptBuilder
from .optimizer import PromptOptimizer
from .examples import FewShotExamples

__all__ = [
    'PromptTemplates',
    'PromptBuilder', 
    'PromptOptimizer',
    'FewShotExamples'
]

# Version info
__version__ = '2.0.0'
PROMPT_VERSION = 'v2'