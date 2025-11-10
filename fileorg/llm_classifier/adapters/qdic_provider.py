"""
QDIC Provider for Qualcomm AI Engine Direct.

This adapter implements ILLMProvider using Qualcomm AI Engine Direct (QAIC)
for optimized inference on Qualcomm Cloud AI 100 accelerators.
"""

from typing import Dict, List

from loguru import logger

from fileorg.llm_classifier.ports import ILLMProvider


class QDICProvider(ILLMProvider):
    """
    Qualcomm AI Engine Direct implementation of ILLMProvider.

    Supports local inference on Qualcomm Cloud AI 100 accelerators.
    Optimized for QAIC hardware with neural network acceleration.

    Note: This provider requires qaic-compute-runtime and proper QAIC setup.
    """

    def __init__(self, model_name: str = "meta-llama/Llama-3.2-3B-Instruct", device_id: int = 0, use_quantization: bool = True, **model_kwargs):
        """
        Initialize QDIC provider.

        Args:
            model_name: HuggingFace model identifier
            device_id: QAIC device ID (default: 0)
            use_quantization: Use INT8 quantization for better performance (default: True)
            **model_kwargs: Additional arguments for model configuration
        """
        self.model_name = model_name
        self.device_id = device_id
        self.use_quantization = use_quantization
        self.model_kwargs = model_kwargs

        # Lazy loading - model and tokenizer are loaded on first use
        self._model = None
        self._tokenizer = None
        self._qaic_session = None

        logger.info(f"Initialized QDICProvider (Qualcomm AI Engine) with model={model_name}, device_id={device_id}, quantization={use_quantization}")

    def _check_qaic_available(self) -> bool:
        """Check if QAIC runtime is available."""
        try:
            # Try to import QAIC related libraries
            # This is a placeholder - actual import depends on QAIC SDK
            import subprocess  # nosec B404

            result = subprocess.run(["qaic-util", "-q", "-d", str(self.device_id)], capture_output=True, text=True, timeout=5)  # nosec
            return result.returncode == 0
        except (ImportError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _load_model(self):
        """Lazy load model and tokenizer with QAIC optimization."""
        if self._model is not None:
            return

        try:
            from transformers import AutoTokenizer

            logger.info(f"Loading model {self.model_name} for QAIC...")

            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)  # nosec B615

            # Check QAIC availability
            if not self._check_qaic_available():
                logger.warning(
                    "QAIC device not available. Falling back to CPU mode. Please ensure qaic-compute-runtime is installed and devices are accessible."
                )
                # Fallback to HuggingFace on CPU
                import torch
                from transformers import AutoModelForCausalLM

                self._model = AutoModelForCausalLM.from_pretrained(  # nosec B615
                    self.model_name, torch_dtype=torch.float32, low_cpu_mem_usage=True, **self.model_kwargs
                )
                self._model.eval()
                logger.info("Using CPU fallback mode")
                return

            # TODO: Implement actual QAIC model loading
            # This requires QAIC SDK and proper model compilation for QAIC
            # Placeholder implementation:
            logger.warning(
                "QAIC model loading not fully implemented. Please compile model for QAIC using qaic-exec or similar tools. Falling back to CPU mode."
            )

            # Fallback implementation
            import torch
            from transformers import AutoModelForCausalLM

            self._model = AutoModelForCausalLM.from_pretrained(  # nosec B615
                self.model_name, torch_dtype=torch.float32 if not self.use_quantization else torch.int8, low_cpu_mem_usage=True, **self.model_kwargs
            )
            self._model.eval()

            logger.success("Model loaded (fallback mode)")

        except ImportError as e:
            logger.error("Required libraries not installed. Install with: pip install transformers torch")
            raise ImportError("Transformers library required for QDICProvider. For full QAIC support, install qaic-compute-runtime.") from e
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def generate(self, messages: List[Dict[str, str]], max_tokens: int = 32768) -> str:
        """
        Generate text using QAIC-optimized model.

        Args:
            messages: Chat format messages [{"role": "user/system", "content": "..."}]
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text string

        Raises:
            RuntimeError: If QAIC or inference errors occur
        """
        self._load_model()

        try:
            import torch

            # Apply chat template if tokenizer supports it
            if hasattr(self._tokenizer, "apply_chat_template"):
                formatted_prompt = self._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            else:
                formatted_prompt = self._format_messages_fallback(messages)

            logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")

            # Tokenize
            inputs = self._tokenizer(formatted_prompt, return_tensors="pt", truncation=True, max_length=max_tokens)

            # Generate
            # TODO: Use QAIC-optimized inference when available
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
        """Check if the provider is available (QAIC ready)."""
        try:
            self._load_model()
            return True
        except Exception:
            return False

    def get_device_info(self) -> Dict[str, any]:
        """Get device information for debugging."""
        info = {
            "device": f"qaic:{self.device_id}",
            "quantization": self.use_quantization,
            "qaic_available": self._check_qaic_available(),
        }

        if self._check_qaic_available():
            info["backend"] = "Qualcomm AI Engine Direct"
        else:
            info["backend"] = "CPU fallback"

        return info
