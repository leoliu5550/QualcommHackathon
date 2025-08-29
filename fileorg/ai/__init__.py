"""FileOrg AI Module.

Provides AI backend interfaces for document classification and organization.
"""

from fileorg.ai.interface import get_llm, BaseLLM, LocalTransformersLLM, QualcommLLM
from fileorg.ai.config import Config, config, update_default_config

__all__ = [
    "get_llm",
    "BaseLLM",
    "LocalTransformersLLM",
    "QualcommLLM",
    "Config",
    "config",
    "update_default_config",
]