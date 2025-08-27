"""
File Classification Module

Provides intelligent document classification and folder naming with
advanced prompt engineering capabilities.
"""

from .classifier import CreateFolderNamer, get_create_name, create_name
from .prompt_engine import (
    PromptBuilder,
    PromptOptimizer,
    PromptTemplates,
    FewShotExamples
)

__all__ = [
    'CreateFolderNamer',
    'create_name',
    'get_create_name',
    'PromptBuilder',
    'PromptOptimizer',
    'PromptTemplates',
    'FewShotExamples'
]

# Version info
__version__ = '2.0.0'
CLASSIFIER_VERSION = 'v2'