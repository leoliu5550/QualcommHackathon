"""
LLM Factory Adapter

Factory for creating LLM adapter instances based on backend type.

SOLID Principles:
    - Single Responsibility: Only creates LLM adapters
    - Open/Closed: Open for extension with new backends
    - Dependency Inversion: Returns abstract LLMPort
"""

from typing import Dict, Any
from fileorg.llm_classifier.ports import LLMPort, LLMFactoryPort
from fileorg.llm_classifier.adapters.llm.qualcomm_adapter import QualcommLLMAdapter
from fileorg.llm_classifier.adapters.llm.local_adapter import LocalTransformersAdapter


class LLMFactory(LLMFactoryPort):
    """
    Factory for creating LLM adapter instances.

    Supports multiple backends: Qualcomm NPU, local transformers, etc.
    """

    def create_llm(
        self,
        backend: str,
        config: Dict[str, Any]
    ) -> LLMPort:
        """
        Create an LLM adapter based on backend type.

        Args:
            backend: Backend identifier ('qualcomm', 'local')
            config: Backend-specific configuration

        Returns:
            LLM adapter instance implementing LLMPort

        Raises:
            ValueError: If backend is not supported
        """
        if backend == "qualcomm":
            return QualcommLLMAdapter(
                api_key=config.get("api_key"),
                api_url=config.get("api_url", "http://127.0.0.1:80/v1.0/chat/completions"),
                model=config.get("model", ".bot/Llama 3.1 8B @NPU"),
                timeout=config.get("timeout", 600.0)
            )
        elif backend == "local":
            return LocalTransformersAdapter(
                model_id=config.get("model_id", "iFaz/llama32_3B_en_emo_2000_stp"),
                device=config.get("device", "cuda"),
                cache_dir=config.get("cache_dir", "./fileorg/llm_classifier/llm/model")
            )
        else:
            raise ValueError(
                f"Unsupported LLM backend: {backend}. "
                f"Supported backends: 'qualcomm', 'local'"
            )


# Convenience function for backward compatibility
def get_llm(backend: str = "qualcomm", **kwargs) -> LLMPort:
    """
    Convenience function to create LLM adapter.

    Args:
        backend: Backend type identifier
        **kwargs: Backend-specific configuration

    Returns:
        LLM adapter instance
    """
    factory = LLMFactory()
    return factory.create_llm(backend, kwargs)
