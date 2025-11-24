"""
MPS Provider for Apple Silicon (M1/M2/M3) using Metal Performance Shaders.

This adapter implements ILLMProvider using HuggingFace transformers library
optimized for Apple Silicon with MPS (Metal Performance Shaders) acceleration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from loguru import logger

from fileorg.llm_classifier.ports.interfaces import ILLMProvider

if TYPE_CHECKING:
    import torch


class MPSProvider(ILLMProvider):
    """
    Metal Performance Shaders (MPS) implementation of ILLMProvider.

    Supports local inference on Apple M1/M2/M3 chips using Metal Performance Shaders.
    Optimized for macOS devices with Apple Silicon.
    """

    def __init__(
        self, model_name: str = "meta-llama/Llama-3.2-3B-Instruct", use_mps: bool = True, dtype: Optional["torch.dtype"] = None, **model_kwargs
    ):
        """
        Initialize MacOS provider.

        Args:
            model_name: HuggingFace model identifier
            use_mps: Use Metal Performance Shaders if available (default: True)
            dtype: Torch data type (default: float16 for MPS)
            **model_kwargs: Additional arguments passed to AutoModelForCausalLM.from_pretrained
        """
        import torch  # noqa: F401 - Import here to fail fast if torch is not installed

        self.model_name = model_name
        self.use_mps = use_mps
        self.device = self._get_device()
        self.dtype = dtype or self._get_dtype()
        self.model_kwargs = model_kwargs

        # Lazy loading - model and tokenizer are loaded on first use
        self._model = None
        self._tokenizer = None

        logger.info(f"Initialized MPSProvider (Metal Performance Shaders) with model={model_name}, device={self.device}, dtype={self.dtype}")

    def _get_device(self) -> str:
        """Auto-detect best available device for macOS."""
        import torch

        if self.use_mps and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _get_dtype(self) -> "torch.dtype":
        """Auto-detect best dtype based on device."""
        import torch

        if self.device == "mps":
            # MPS works best with float16
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
                    low_cpu_mem_usage=True,  # Important for MPS
                    local_files_only=True,
                    **self.model_kwargs,
                )  # nosec B615
                logger.success(f"Model loaded from cache on {self.device}")

            except (OSError, ValueError) as cache_error:
                # Cache miss - download model
                logger.warning(f"Cache miss: {cache_error}. Downloading model...")
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)  # nosec B615

                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    dtype=self.dtype,
                    low_cpu_mem_usage=True,  # Important for MPS
                    **self.model_kwargs,
                )  # nosec B615
                logger.success(f"Model downloaded and loaded on {self.device}")

            # Move to device
            self._model = self._model.to(self.device)
            self._model.eval()  # Set to evaluation mode

        except ImportError as e:
            logger.error("transformers library not installed. Install with: pip install transformers torch")
            raise ImportError("HuggingFace transformers required for MPSProvider. Install with: pip install transformers torch") from e
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate(self, messages: List[Dict[str, str]], max_tokens: int = 32768) -> str:
        """
        Generate text using Apple Silicon optimized model.

        Args:
            messages: Chat format messages [{"role": "user/system", "content": "..."}]
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text string

        Raises:
            RuntimeError: If MPS OOM or other inference errors occur
        """
        self._load_model()

        try:
            # Apply chat template if tokenizer supports it
            if hasattr(self._tokenizer, "apply_chat_template"):
                formatted_prompt = self._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            else:
                formatted_prompt = self._format_messages_fallback(messages)

            logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")

            # Tokenize
            inputs = self._tokenizer(formatted_prompt, return_tensors="pt", truncation=True, max_length=max_tokens).to(self.device)

            # Generate
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=min(max_tokens, 2048),
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self._tokenizer.eos_token_id,
                )

            # Decode only the generated part
            generated_ids = outputs[0][inputs["input_ids"].shape[1] :]
            generated_text = self._tokenizer.decode(generated_ids, skip_special_tokens=True)

            logger.debug(f"Generated {len(generated_text)} characters")

            return generated_text

        except RuntimeError as e:
            if "MPS" in str(e):
                logger.error("MPS backend error - try reducing max_tokens")
                raise RuntimeError(f"MPS backend error: {e}") from e
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
        """Check if the provider is available (MPS/CPU ready)."""
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
            "mps_available": torch.backends.mps.is_available(),
        }

        if self.device == "mps":
            info["backend"] = "Metal Performance Shaders"

        return info
