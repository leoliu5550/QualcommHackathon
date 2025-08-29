"""
File Classification Module

Provides intelligent document classification and folder naming with
centralized prompt version management.
"""

from .classifier import CreateFolderNamer, get_create_name, create_name
from .prompt_versions import (
    get_prompt_version,
    get_version_features,
    detect_domain,
    list_versions,
    DEFAULT_VERSION,
    SUPPORTED_VERSIONS
)

__all__ = [
    'CreateFolderNamer',
    'create_name',
    'get_create_name',
    'get_prompt_version',
    'get_version_features',
    'detect_domain',
    'list_versions',
    'DEFAULT_VERSION',
    'SUPPORTED_VERSIONS'
]

# Version info
__version__ = '2.0.0'
CLASSIFIER_VERSION = DEFAULT_VERSION