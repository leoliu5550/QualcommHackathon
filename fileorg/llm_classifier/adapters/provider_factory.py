"""
Provider Factory for automatic LLM provider selection.

This module provides a factory to automatically select the best available
LLM provider based on the current hardware platform.
"""

import platform
import subprocess  # nosec B404: Only used for hardware detection, no user input
from typing import Optional

from loguru import logger

from fileorg.llm_classifier.adapters.gpu_provider import GPUProvider
from fileorg.llm_classifier.adapters.mps_provider import MPSProvider
from fileorg.llm_classifier.adapters.qdic_provider import QDICProvider
from fileorg.llm_classifier.ports import ILLMProvider


class ProviderFactory:
    """
    Factory for creating the appropriate LLM provider based on hardware.

    Automatically detects available hardware and selects the best provider:
    1. Qualcomm AI Engine (QAIC) - if available
    2. NVIDIA CUDA GPU - if available
    3. Apple Silicon (MPS) - if on macOS with Apple Silicon
    4. CPU fallback

    Usage:
        # Automatic selection
        provider = ProviderFactory.create()

        # Explicit selection
        provider = ProviderFactory.create(provider_type="gpu")   # NVIDIA
        provider = ProviderFactory.create(provider_type="mps")   # Apple Silicon
        provider = ProviderFactory.create(provider_type="qaic")  # Qualcomm

        # With custom model
        provider = ProviderFactory.create(
            model_name="meta-llama/Llama-3.2-8B-Instruct"
        )
    """

    @staticmethod
    def _check_qaic_available() -> bool:
        """Check if QAIC is available."""
        try:
            result = subprocess.run(["qaic-util", "-q"], capture_output=True, text=True, timeout=5)  # nosec
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def _check_cuda_available() -> bool:
        """Check if CUDA is available."""
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    @staticmethod
    def _check_mps_available() -> bool:
        """Check if Apple Metal Performance Shaders is available."""
        try:
            import torch

            return platform.system() == "Darwin" and torch.backends.mps.is_available()
        except ImportError:
            return False

    @staticmethod
    def _detect_best_provider() -> str:
        """
        Auto-detect the best available provider.

        Priority:
        1. QAIC (Qualcomm AI Engine)
        2. CUDA (NVIDIA GPU)
        3. MPS (Apple Silicon)
        4. CPU (fallback)
        """
        if ProviderFactory._check_qaic_available():
            logger.info("Detected Qualcomm AI Engine (QAIC)")
            return "qaic"

        if ProviderFactory._check_cuda_available():
            logger.info("Detected NVIDIA CUDA GPU")
            return "gpu"

        if ProviderFactory._check_mps_available():
            logger.info("Detected Apple Silicon (MPS)")
            return "mps"

        logger.info("No accelerator detected, using CPU fallback")
        return "cpu"

    @staticmethod
    def create(provider_type: Optional[str] = None, model_name: str = "meta-llama/Llama-3.2-3B-Instruct", **kwargs) -> ILLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_type: Explicit provider type ("gpu", "mps", "qaic", "cpu")
                          If None, auto-detects the best provider
            model_name: HuggingFace model identifier
            **kwargs: Additional arguments passed to the provider

        Returns:
            ILLMProvider instance

        Raises:
            ValueError: If the specified provider_type is invalid
            RuntimeError: If the requested provider is not available

        Examples:
            # Auto-detect
            provider = ProviderFactory.create()

            # Explicit NVIDIA GPU
            provider = ProviderFactory.create(provider_type="gpu")

            # Explicit Apple Silicon MPS
            provider = ProviderFactory.create(provider_type="mps")

            # Custom model
            provider = ProviderFactory.create(
                model_name="meta-llama/Llama-3.2-8B-Instruct"
            )
        """
        # Auto-detect if not specified
        if provider_type is None:
            provider_type = ProviderFactory._detect_best_provider()

        provider_type = provider_type.lower()

        # Create the appropriate provider
        if provider_type == "gpu" or provider_type == "cuda":
            if not ProviderFactory._check_cuda_available():
                logger.warning("CUDA not available. Falling back to CPU. GPUProvider will use CPU mode.")
            logger.info(f"Creating GPUProvider with model={model_name}")
            return GPUProvider(model_name=model_name, **kwargs)

        elif provider_type == "mps":
            if not ProviderFactory._check_mps_available():
                logger.warning("MPS not available. Falling back to CPU. MPSProvider will use CPU mode.")
            logger.info(f"Creating MPSProvider with model={model_name}")
            return MPSProvider(model_name=model_name, **kwargs)

        elif provider_type == "qaic" or provider_type == "qualcomm":
            if not ProviderFactory._check_qaic_available():
                logger.warning("QAIC not available. Falling back to CPU. QDICProvider will use CPU mode.")
            logger.info(f"Creating QDICProvider with model={model_name}")
            return QDICProvider(model_name=model_name, **kwargs)

        elif provider_type == "cpu":
            # Use GPUProvider with CPU fallback
            logger.info(f"Creating GPUProvider (CPU mode) with model={model_name}")
            return GPUProvider(model_name=model_name, device="cpu", **kwargs)

        else:
            raise ValueError(f"Invalid provider_type: {provider_type}. Valid options: 'gpu', 'mps', 'qaic', 'cpu', or None for auto-detect")

    @staticmethod
    def get_available_providers() -> dict:
        """
        Get information about all available providers.

        Returns:
            Dict with provider availability and details
        """
        return {
            "qaic": {
                "available": ProviderFactory._check_qaic_available(),
                "name": "Qualcomm AI Engine Direct",
                "description": "Optimized for Qualcomm Cloud AI 100 accelerators",
            },
            "gpu": {
                "available": ProviderFactory._check_cuda_available(),
                "name": "NVIDIA CUDA GPU",
                "description": "Optimized for NVIDIA CUDA-enabled GPUs",
            },
            "mps": {
                "available": ProviderFactory._check_mps_available(),
                "name": "Apple Silicon (MPS)",
                "description": "Optimized for Apple M1/M2/M3 chips with Metal Performance Shaders",
            },
            "cpu": {"available": True, "name": "CPU Fallback", "description": "Works on all platforms (slowest)"},
        }
