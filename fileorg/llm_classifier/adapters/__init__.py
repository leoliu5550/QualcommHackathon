"""
Adapter implementations for LLM classifier.
"""

from fileorg.llm_classifier.adapters.gpu_provider import GPUProvider
from fileorg.llm_classifier.adapters.mps_provider import MPSProvider
from fileorg.llm_classifier.adapters.provider_factory import ProviderFactory
from fileorg.llm_classifier.adapters.qdic_provider import QDICProvider
from fileorg.llm_classifier.adapters.template_loader import Jinja2TemplateLoader

__all__ = [
    # LLM providers
    "GPUProvider",
    "MPSProvider",
    "QDICProvider",
    "ProviderFactory",
    # Utilities
    "Jinja2TemplateLoader",
]
