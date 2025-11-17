"""
GPU Provider for NVIDIA CUDA-enabled GPUs.

This adapter implements ILLMProvider using HuggingFace transformers library
for local NVIDIA GPU inference with Llama models.
"""

from typing import Dict, List, Optional

import torch
from loguru import logger

from fileorg.llm_classifier.ports.interfaces import ILLMProvider


class GPUProvider(ILLMProvider):
    """
    NVIDIA GPU implementation of ILLMProvider.

    Supports local NVIDIA CUDA GPU inference using Llama 3B/8B models.
    Optimized for CUDA-enabled devices.
    """

    def __init__(
        self,
        model_name: str = "meta-llama/Llama-3.2-3B-Instruct",
        device: Optional[str] = None,
        dtype: Optional[torch.dtype] = None,
        **model_kwargs,
    ):
        """
        Initialize HuggingFace provider.

        Args:
            model_name: HuggingFace model identifier
            device: Device to use ('cuda', 'cpu', or None for auto-detection)
            dtype: Torch data type (default: auto-detect based on device)
            **model_kwargs: Additional arguments passed to AutoModelForCausalLM.from_pretrained
        """
        self.model_name = model_name
        self.device = device or self._get_device()
        self.dtype = dtype or self._get_dtype()
        self.model_kwargs = model_kwargs

        # Lazy loading - model and tokenizer are loaded on first use
        self._model = None
        self._tokenizer = None

        logger.info(f"Initialized GPUProvider (NVIDIA CUDA) with model={model_name}, device={self.device}, dtype={self.dtype}")

    def _get_device(self) -> str:
        """Auto-detect best available device."""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _get_dtype(self) -> torch.dtype:
        """Auto-detect best dtype based on device."""
        if self.device == "cuda":
            # Use bfloat16 for GPU if available, else float16
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16
            return torch.float16
        return torch.float32

    def _load_model(self):
        """Lazy load model and tokenizer with cache-first strategy."""
        if self._model is not None:
            return

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(f"Loading model {self.model_name}...")

            # Try to load from local cache first
            try:
                logger.debug("Attempting to load from local cache...")
                # Load tokenizer from cache
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)  # nosec B615

                # Load model from cache
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    dtype=self.dtype,
                    device_map=self.device if self.device == "cuda" else None,
                    local_files_only=True,
                    **self.model_kwargs,
                )  # nosec B615
                logger.success(f"Model loaded from cache on {self.device}")

            except (OSError, ValueError) as cache_error:
                # Cache miss - download model
                logger.warning(f"Cache miss: {cache_error}. Downloading model...")
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)  # nosec B615

                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_name, dtype=self.dtype, device_map=self.device if self.device == "cuda" else None, **self.model_kwargs
                )  # nosec B615
                logger.success(f"Model downloaded and loaded on {self.device}")

            # Move to device if not using device_map
            if self.device != "cuda":
                self._model = self._model.to(self.device)

            self._model.eval()  # Set to evaluation mode

        except ImportError as e:
            logger.error("transformers library not installed. Install with: pip install transformers torch")
            raise ImportError("HuggingFace transformers required for GPUProvider. Install with: pip install transformers torch") from e
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate(self, messages: List[Dict[str, str]], max_tokens: int = 32768) -> str:
        """
        Generate text using HuggingFace model.

        Args:
            messages: Chat format messages [{"role": "user/system", "content": "..."}]
            max_tokens: Maximum tokens to generate (Note: this is for generation, not total)

        Returns:
            Generated text string

        Raises:
            RuntimeError: If GPU OOM or other inference errors occur
        """
        self._load_model()

        try:
            # Apply chat template if tokenizer supports it
            if hasattr(self._tokenizer, "apply_chat_template"):
                # Use tokenizer's chat template
                formatted_prompt = self._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            else:
                # Fallback: concatenate messages
                formatted_prompt = self._format_messages_fallback(messages)

            logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")

            # Tokenize
            inputs = self._tokenizer(formatted_prompt, return_tensors="pt", truncation=True, max_length=max_tokens).to(self.device)

            # Generate
            # For JSON output, we need enough tokens (at least 512 for structured responses)
            generation_tokens = min(max(max_tokens, 512), 2048)
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=generation_tokens,
                    do_sample=False,  # Use greedy decoding for more reliable JSON output
                    temperature=1.0,  # Keep temperature at 1.0 for greedy decoding
                    pad_token_id=self._tokenizer.eos_token_id,
                )

            # Decode only the generated part (exclude input prompt)
            generated_ids = outputs[0][inputs["input_ids"].shape[1] :]
            generated_text = self._tokenizer.decode(generated_ids, skip_special_tokens=True)

            logger.debug(f"Generated {len(generated_text)} characters")

            return generated_text

        except torch.cuda.OutOfMemoryError as e:
            logger.error("GPU Out of Memory error")
            raise RuntimeError("GPU Out of Memory. Try reducing max_tokens or batch size.") from e
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise RuntimeError(f"LLM generation failed: {e}") from e

    def _format_messages_fallback(self, messages: List[Dict[str, str]]) -> str:
        """Fallback message formatting if chat template not available."""
        formatted = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted += f"{role.upper()}: {content}\n\n"
        return formatted.strip()

    def is_available(self) -> bool:
        """Check if the provider is available (GPU/CPU ready)."""
        try:
            self._load_model()
            return True
        except Exception:
            return False

    def get_device_info(self) -> Dict[str, any]:
        """Get device information for debugging."""
        info = {
            "device": self.device,
            "dtype": str(self.dtype),
            "cuda_available": torch.cuda.is_available(),
        }

        if torch.cuda.is_available():
            info.update(
                {
                    "cuda_device_count": torch.cuda.device_count(),
                    "cuda_device_name": torch.cuda.get_device_name(0),
                    "cuda_memory_allocated": torch.cuda.memory_allocated(0),
                    "cuda_memory_reserved": torch.cuda.memory_reserved(0),
                }
            )

        return info
