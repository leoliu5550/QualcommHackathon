"""
LLM provider adapters for different hardware platforms.

These adapters implement ILLMProvider for various acceleration platforms.
"""

from .gpu_provider import GPUProvider
from .mps_provider import MPSProvider
from .qdic_provider import QDICProvider

__all__ = ["GPUProvider", "MPSProvider", "QDICProvider"]
