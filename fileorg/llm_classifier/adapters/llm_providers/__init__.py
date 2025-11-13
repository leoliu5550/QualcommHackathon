"""
LLM provider adapters for different hardware platforms.

These adapters implement ILLMProvider for various acceleration platforms.
"""

from typing import List

__all__: List[str] = []

# Conditionally import providers based on available dependencies
# This prevents import errors in CI/test environments where optional dependencies might not be installed

try:
    from .gpu_provider import GPUProvider  # noqa: F401

    __all__.append("GPUProvider")
except ImportError:
    # torch not available - GPU provider will not be available
    pass

try:
    from .mps_provider import MPSProvider  # noqa: F401

    __all__.append("MPSProvider")
except ImportError:
    # MPS-specific dependencies not available
    pass

try:
    from .qdic_provider import QDICProvider  # noqa: F401

    __all__.append("QDICProvider")
except ImportError:
    # QDIC-specific dependencies not available
    pass
