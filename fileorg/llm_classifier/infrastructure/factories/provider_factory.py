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
    1. TURU (Local API server) - if available
    2. ONNX (Lightweight inference) - if model exported
    3. Qualcomm AI Engine (QAIC) - if available
    4. NVIDIA CUDA GPU - if available
    5. Apple Silicon (MPS) - if on macOS with Apple Silicon
    6. CPU fallback

    Usage:
        # Automatic selection (recommended)
        provider = ProviderFactory.create()

        # Explicit ONNX (lightweight, fast)
        provider = ProviderFactory.create(provider_type="onnx")

        # Explicit hardware providers
        provider = ProviderFactory.create(provider_type="gpu")   # NVIDIA
        provider = ProviderFactory.create(provider_type="mps")   # Apple Silicon
        provider = ProviderFactory.create(provider_type="qaic")  # Qualcomm

        # TURU API server
        provider = ProviderFactory.create(provider_type="turu")

        # With custom model (for torch-based providers)
        provider = ProviderFactory.create(
            provider_type="gpu",
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

            with httpx.Client(timeout=1.0) as client:
                response = client.get("http://127.0.0.1:8000/v1/models")
                return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _validate_model_dir(model_dir) -> bool:
        """
        Check if a directory contains a valid ONNX model.

        Args:
            model_dir: Path to model directory

        Returns:
            True if directory contains valid ONNX model, False otherwise
        """
        if not model_dir.exists() or not model_dir.is_dir():
            return False

        # Check for required files
        onnx_files = list(model_dir.glob("*.onnx"))
        tokenizer_file = model_dir / "tokenizer.json"

        return len(onnx_files) > 0 and tokenizer_file.exists()

    @staticmethod
    def _check_onnx_available() -> bool:
        """
        Check if ONNX Runtime and model files are available.

        Auto-detection strategy:
        1. Check environment variable ONNX_MODEL_NAME
        2. Scan models/ directory for any exported models
        3. If multiple models found, select most recently modified
        """
        try:
            import os
            from pathlib import Path

            import onnxruntime  # noqa: F401

            models_base_dir = Path(__file__).parent.parent.parent / "models"

            # Strategy 1: Check environment variable
            model_name = os.getenv("ONNX_MODEL_NAME")
            if model_name:
                model_dir = models_base_dir / model_name
                if ProviderFactory._validate_model_dir(model_dir):
                    logger.info(f"Using ONNX model from ONNX_MODEL_NAME: {model_name}")
                    return True
                else:
                    logger.warning(f"ONNX_MODEL_NAME set to '{model_name}' but model not found or invalid")

            # Strategy 2: Scan models/ directory for any exported models
            if not models_base_dir.exists():
                return False

            valid_models = []
            for item in models_base_dir.iterdir():
                if item.is_dir() and ProviderFactory._validate_model_dir(item):
                    # Get last modification time
                    mtime = item.stat().st_mtime
                    valid_models.append((item, mtime))

            if not valid_models:
                logger.debug("No ONNX models found in models/ directory")
                return False

            # Sort by modification time (most recent first)
            valid_models.sort(key=lambda x: x[1], reverse=True)
            selected_model = valid_models[0][0]

            if len(valid_models) > 1:
                logger.info(f"Found {len(valid_models)} ONNX models, selected most recent: {selected_model.name}")
            else:
                logger.info(f"Auto-detected ONNX model: {selected_model.name}")

            return True

        except ImportError:
            return False

    @staticmethod
    def _detect_best_provider() -> str:
        """
        Auto-detect the best available provider.

        Priority:
        1. TURU (Local API server) - Recommended for production
        2. ONNX (Lightweight inference) - Fast, multi-platform
        3. QAIC (Qualcomm AI Engine)
        4. CUDA (NVIDIA GPU)
        5. MPS (Apple Silicon)
        6. CPU (fallback)
        """
        if ProviderFactory._check_turu_available():
            logger.info("Detected TURU API server")
            return "turu"

        if ProviderFactory._check_onnx_available():
            logger.info("Detected ONNX Runtime with exported model")
            return "onnx"

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

        # Create the appropriate provider with fallback support
        if provider_type == "onnx":
            logger.info("Creating OnnxProvider (ONNX Runtime)")
            try:
                from fileorg.llm_classifier.adapters.llm_providers.onnx_provider import OnnxProvider

                provider = OnnxProvider(**kwargs)

                # Test if provider is available
                if not provider.is_available():
                    raise RuntimeError("OnnxProvider not available (model or tokenizer not found)")

                logger.success("OnnxProvider created successfully")
                return provider

            except Exception as e:
                logger.warning(f"OnnxProvider failed: {e}")
                logger.info("Falling back to hardware-specific provider...")

                # Fallback to best available torch-based provider
                fallback_type = None
                if ProviderFactory._check_cuda_available():
                    fallback_type = "gpu"
                elif ProviderFactory._check_mps_available():
                    fallback_type = "mps"
                elif ProviderFactory._check_qaic_available():
                    fallback_type = "qaic"
                else:
                    fallback_type = "cpu"

                logger.info(f"Using fallback provider: {fallback_type}")
                return ProviderFactory.create(provider_type=fallback_type, model_name=model_name, **kwargs)

        elif provider_type == "turu":
            logger.info("Creating TURUProvider")
            try:
                import os

                from fileorg.llm_classifier.adapters.llm_providers.turu_provider import TURUProvider

                # Load TURU configuration from environment variables
                turu_config = {
                    "api_key": os.getenv("TURU_API_KEY", "API_KEY"),
                    "base_url": os.getenv("TURU_BASE_URL", "http://127.0.0.1:8000/v1"),
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
                error_msg = (
                    f"No LLM provider available. Please choose one of:\n\n"
                    f"Option 1 - Lightweight ONNX Runtime (Recommended for production):\n"
                    f"  1. Install export dependencies: pip install -e '.[llm-export]' or uv pip install -e '.[llm-export]'\n"
                    f"  2. Export model: fileorg-export-llm\n"
                    f"  3. Run again (will use ONNX automatically)\n\n"
                    f"Option 2 - TURU API Server:\n"
                    f"  1. Start TURU API server at http://127.0.0.1:8000\n"
                    f"  2. Run again (will detect TURU automatically)\n\n"
                    f"Option 3 - PyTorch-based providers (Heavy dependencies):\n"
                    f"  1. Install torch: pip install -e '.[non-npu]' or uv pip install -e '.[non-npu]'\n"
                    f"  2. Run again\n\n"
                    f"Original error: {e}"
                )
                raise RuntimeError(error_msg) from e

        else:
            raise ValueError(
                f"Invalid provider_type: {provider_type}. Valid options: 'turu', 'onnx', 'gpu', 'mps', 'qaic', 'cpu', or None for auto-detect"
            )

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
                "description": "Local HTTP API server (recommended for production)",
                "priority": 1,
            },
            "onnx": {
                "available": ProviderFactory._check_onnx_available(),
                "name": "ONNX Runtime",
                "description": "Lightweight, fast, multi-platform (5-10x faster startup)",
                "priority": 2,
            },
            "qaic": {
                "available": ProviderFactory._check_qaic_available(),
                "name": "Qualcomm AI Engine Direct",
                "description": "Optimized for Qualcomm Cloud AI 100 accelerators",
                "priority": 3,
            },
            "gpu": {
                "available": ProviderFactory._check_cuda_available(),
                "name": "NVIDIA CUDA GPU",
                "description": "Optimized for NVIDIA CUDA-enabled GPUs (requires torch)",
                "priority": 4,
            },
            "mps": {
                "available": ProviderFactory._check_mps_available(),
                "name": "Apple Silicon (MPS)",
                "description": "Optimized for Apple M1/M2/M3 chips (requires torch)",
                "priority": 5,
            },
            "cpu": {
                "available": True,
                "name": "CPU Fallback",
                "description": "Works on all platforms (slowest, requires torch)",
                "priority": 6,
            },
        }
