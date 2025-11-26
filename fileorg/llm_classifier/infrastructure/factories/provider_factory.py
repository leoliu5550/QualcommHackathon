"""
Provider Factory for automatic LLM provider selection.

This module provides a factory to automatically select the best available
LLM provider based on the current hardware platform.
"""

import platform
import subprocess  # nosec B404: Only used for hardware detection, no user input
from typing import Optional

from loguru import logger

from fileorg.llm_classifier.ports.interfaces import ILLMProvider


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
    def _check_turu_available() -> bool:
        """Check if TURU API server is available."""
        try:
            import httpx
        except ImportError:
            logger.debug("httpx not installed, TURU provider unavailable")
            return False

        try:
            import os

            base_url = os.getenv("TURU_BASE_URL", "http://127.0.0.1:80/v1.0")
            models_url = f"{base_url}/models"

            with httpx.Client(timeout=2.0) as client:
                response = client.get(models_url)
                return response.status_code == 200
        except httpx.ConnectError:
            logger.debug(f"Cannot connect to TURU server at {base_url}")
            return False
        except Exception as e:
            logger.debug(f"TURU check failed: {e}")
            return False

    @staticmethod
    def _detect_best_provider() -> str:
        """
        Auto-detect the best available provider.

        Priority:
        1. TURU (Local API server)
        2. QAIC (Qualcomm AI Engine)
        3. CUDA (NVIDIA GPU)
        4. MPS (Apple Silicon)
        5. CPU (fallback)
        """
        if ProviderFactory._check_turu_available():
            logger.info("Detected TURU API server")
            return "turu"

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
        if provider_type == "turu":
            logger.info("Creating TURUProvider")
            try:
                import os

                from fileorg.llm_classifier.adapters.llm_providers.turu_provider import TURUProvider

                # Load TURU configuration from environment variables
                turu_config = {
                    "api_key": os.getenv("TURU_API_KEY", "API_KEY"),
                    "base_url": os.getenv("TURU_BASE_URL", "http://127.0.0.1:80/v1.0"),
                    "model": os.getenv("TURU_MODEL", ".bot/Llama 3.1 8B @NPU"),
                    "temperature": float(os.getenv("TURU_TEMPERATURE", "0.1")),
                    "timeout": float(os.getenv("TURU_TIMEOUT", "600.0")),
                }

                # Override with any kwargs provided
                turu_config.update(kwargs)

                logger.info(f"TURU config: model={turu_config['model']}, url={turu_config['base_url']}")
                return TURUProvider(**turu_config)
            except ImportError as e:
                raise RuntimeError(f"TURUProvider not available: {e}") from e

        elif provider_type == "gpu" or provider_type == "cuda":
            if not ProviderFactory._check_cuda_available():
                logger.warning("CUDA not available. Falling back to CPU. GPUProvider will use CPU mode.")
            logger.info(f"Creating GPUProvider with model={model_name}")
            try:
                from fileorg.llm_classifier.adapters.llm_providers.gpu_provider import GPUProvider

                return GPUProvider(model_name=model_name, **kwargs)
            except ImportError as e:
                raise RuntimeError(f"GPUProvider not available: {e}") from e

        elif provider_type == "mps":
            if not ProviderFactory._check_mps_available():
                logger.warning("MPS not available. Falling back to CPU. MPSProvider will use CPU mode.")
            logger.info(f"Creating MPSProvider with model={model_name}")
            try:
                from fileorg.llm_classifier.adapters.llm_providers.mps_provider import MPSProvider

                return MPSProvider(model_name=model_name, **kwargs)
            except ImportError as e:
                raise RuntimeError(f"MPSProvider not available: {e}") from e

        elif provider_type == "qaic" or provider_type == "qualcomm":
            if not ProviderFactory._check_qaic_available():
                logger.warning("QAIC not available. Falling back to CPU. QDICProvider will use CPU mode.")
            logger.info(f"Creating QDICProvider with model={model_name}")
            try:
                from fileorg.llm_classifier.adapters.llm_providers.qdic_provider import QDICProvider

                return QDICProvider(model_name=model_name, **kwargs)
            except ImportError as e:
                raise RuntimeError(f"QDICProvider not available: {e}") from e

        elif provider_type == "cpu":
            # Use GPUProvider with CPU fallback
            logger.info(f"Creating GPUProvider (CPU mode) with model={model_name}")
            try:
                from fileorg.llm_classifier.adapters.llm_providers.gpu_provider import GPUProvider

                return GPUProvider(model_name=model_name, device="cpu", **kwargs)
            except ImportError as e:
                # Check what's missing and provide specific guidance
                missing_deps = []
                try:
                    import httpx  # noqa: F401
                except ImportError:
                    missing_deps.append("httpx (for TURU)")

                try:
                    import torch  # noqa: F401
                except ImportError:
                    missing_deps.append("torch (for CPU/GPU mode)")

                if missing_deps:
                    deps_str = ", ".join(missing_deps)
                    error_msg = (
                        f"No LLM provider available. Missing dependencies: {deps_str}\n\n"
                        f"For TURU (recommended):\n"
                        f"  1. Install httpx: pip install httpx\n"
                        f"  2. Start TURU API server at http://127.0.0.1:8000\n\n"
                        f"For CPU/GPU mode:\n"
                        f"  Install torch: pip install torch\n"
                        f"\nOriginal error: {e}"
                    )
                else:
                    error_msg = (
                        f"No LLM provider available. Please either:\n"
                        f"  1. Start TURU API server at http://127.0.0.1:8000\n"
                        f"  2. Install torch: pip install torch\n"
                        f"\nOriginal error: {e}"
                    )
                raise RuntimeError(error_msg) from e

        else:
            raise ValueError(f"Invalid provider_type: {provider_type}. Valid options: 'turu', 'gpu', 'mps', 'qaic', 'cpu', or None for auto-detect")

    @staticmethod
    def get_available_providers() -> dict:
        """
        Get information about all available providers.

        Returns:
            Dict with provider availability and details
        """
        return {
            "turu": {
                "available": ProviderFactory._check_turu_available(),
                "name": "TURU API Server",
                "description": "Local HTTP API server (recommended)",
            },
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
