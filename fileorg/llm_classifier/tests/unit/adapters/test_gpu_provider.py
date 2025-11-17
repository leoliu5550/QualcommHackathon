"""
Unit tests for GPUProvider.

Tests verify that GPUProvider correctly implements the ILLMProvider interface
and properly handles basic initialization and configuration.
"""

from unittest.mock import patch

import pytest

# Skip entire module if GPU dependencies are not available
pytest.importorskip("torch")
pytest.importorskip("transformers")

import torch

from fileorg.llm_classifier.adapters.llm_providers import GPUProvider
from fileorg.llm_classifier.ports import ILLMProvider


class TestGPUProviderInterface:
    """Test that GPUProvider correctly implements ILLMProvider interface."""

    def test_implements_interface(self):
        """Verify GPUProvider implements ILLMProvider."""
        provider = GPUProvider()
        assert isinstance(provider, ILLMProvider)

    def test_has_generate_method(self):
        """Verify generate method exists and is callable."""
        provider = GPUProvider()
        assert hasattr(provider, "generate")
        assert callable(provider.generate)


class TestInitialization:
    """Test GPUProvider initialization."""

    @patch("fileorg.llm_classifier.adapters.llm_providers.gpu_provider.logger")
    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.is_bf16_supported", return_value=True)
    def test_default_initialization(self, mock_bf16, mock_cuda, mock_logger):
        """Should initialize with default parameters."""
        provider = GPUProvider()

        assert provider.model_name == "meta-llama/Llama-3.2-3B-Instruct"
        assert provider.device == "cuda"
        assert provider.torch_dtype == torch.bfloat16
        assert provider._model is None
        assert provider._tokenizer is None

        # Verify logging
        mock_logger.info.assert_called_once()

    @patch("fileorg.llm_classifier.adapters.llm_providers.gpu_provider.logger")
    def test_custom_model_initialization(self, mock_logger):
        """Should initialize with custom model name."""
        custom_model = "custom/model-name"
        provider = GPUProvider(model_name=custom_model)

        assert provider.model_name == custom_model

    @patch("fileorg.llm_classifier.adapters.llm_providers.gpu_provider.logger")
    def test_custom_device_initialization(self, mock_logger):
        """Should initialize with custom device."""
        provider = GPUProvider(device="cpu")

        assert provider.device == "cpu"

    @patch("fileorg.llm_classifier.adapters.llm_providers.gpu_provider.logger")
    def test_custom_dtype_initialization(self, mock_logger):
        """Should initialize with custom dtype."""
        provider = GPUProvider(torch_dtype=torch.float32)

        assert provider.torch_dtype == torch.float32

    @patch("fileorg.llm_classifier.adapters.llm_providers.gpu_provider.logger")
    def test_model_kwargs_initialization(self, mock_logger):
        """Should store additional model kwargs."""
        provider = GPUProvider(load_in_8bit=True, max_memory={0: "10GB"})

        assert "load_in_8bit" in provider.model_kwargs
        assert provider.model_kwargs["load_in_8bit"] is True

@pytest.mark.gpu
@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available on this machine")
class TestDeviceDetection:
    """Test device detection logic."""

    @patch("torch.cuda.is_available", return_value=True)
    def test_get_device_cuda_available(self, mock_cuda):
        """Should detect CUDA when available."""
        provider = GPUProvider()
        device = provider._get_device()

        assert device == "cuda"
        mock_cuda.assert_called()

    @patch("torch.cuda.is_available", return_value=False)
    def test_get_device_cuda_not_available(self, mock_cuda):
        """Should fallback to CPU when CUDA not available."""
        provider = GPUProvider()
        device = provider._get_device()

        assert device == "cpu"


class TestDtypeDetection:
    """Test dtype detection logic."""

    @patch("torch.cuda.is_bf16_supported", return_value=True)
    def test_get_dtype_cuda_bfloat16_supported(self, mock_bf16):
        """Should use bfloat16 when supported on CUDA."""
        provider = GPUProvider(device="cuda")
        dtype = provider._get_dtype()

        assert dtype == torch.bfloat16

    @patch("torch.cuda.is_bf16_supported", return_value=False)
    def test_get_dtype_cuda_bfloat16_not_supported(self, mock_bf16):
        """Should use float16 when bfloat16 not supported on CUDA."""
        provider = GPUProvider(device="cuda")
        dtype = provider._get_dtype()

        assert dtype == torch.float16

    def test_get_dtype_cpu(self):
        """Should use float32 for CPU."""
        provider = GPUProvider(device="cpu")
        dtype = provider._get_dtype()

        assert dtype == torch.float32


class TestMessageFormatting:
    """Test message formatting fallback."""

    def test_format_messages_single_message(self):
        """Should format single message correctly."""
        provider = GPUProvider()
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        formatted = provider._format_messages_fallback(messages)

        assert "USER:" in formatted
        assert "Hello, how are you?" in formatted

    def test_format_messages_multiple_messages(self):
        """Should format multiple messages correctly."""
        provider = GPUProvider()
        messages = [{"role": "system", "content": "You are a helpful assistant"}, {"role": "user", "content": "Hello"}]

        formatted = provider._format_messages_fallback(messages)

        assert "SYSTEM:" in formatted
        assert "USER:" in formatted
        assert "helpful assistant" in formatted
        assert "Hello" in formatted

    def test_format_messages_empty_role(self):
        """Should handle missing role field."""
        provider = GPUProvider()
        messages = [{"content": "Hello"}]

        formatted = provider._format_messages_fallback(messages)

        assert "USER:" in formatted  # Default to user

    def test_format_messages_empty_content(self):
        """Should handle missing content field."""
        provider = GPUProvider()
        messages = [{"role": "user"}]

        formatted = provider._format_messages_fallback(messages)

        assert "USER:" in formatted

@pytest.mark.gpu
@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available on this machine")
class TestGetDeviceInfo:
    """Test device information retrieval."""

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.device_count", return_value=2)
    @patch("torch.cuda.get_device_name", return_value="NVIDIA RTX 4090")
    @patch("torch.cuda.memory_allocated", return_value=1024**3)
    @patch("torch.cuda.memory_reserved", return_value=2 * 1024**3)
    @patch("torch.cuda.is_bf16_supported", return_value=True)
    @patch("torch.cuda.current_device", return_value=0)
    def test_get_device_info_cuda(self, mock_current, mock_bf16, mock_mem_res, mock_mem_alloc, mock_name, mock_count, mock_cuda):
        """Should return complete device info for CUDA."""
        provider = GPUProvider(device="cuda")
        info = provider.get_device_info()

        assert info["device"] == "cuda"
        assert "dtype" in info
        assert info["cuda_available"] is True
        assert info["cuda_device_count"] == 2
        assert info["cuda_device_name"] == "NVIDIA RTX 4090"

    @patch("torch.cuda.is_available", return_value=False)
    def test_get_device_info_cpu(self, mock_cuda):
        """Should return basic device info for CPU."""
        provider = GPUProvider(device="cpu")
        info = provider.get_device_info()

        assert info["device"] == "cpu"
        assert info["cuda_available"] is False
        assert "cuda_device_count" not in info
