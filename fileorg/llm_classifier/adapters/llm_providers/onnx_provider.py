"""
ONNX Provider for hardware-accelerated inference.

This adapter implements ILLMProvider using ONNX Runtime for lightweight inference
across multiple hardware platforms (NVIDIA GPU, Apple Silicon, Qualcomm NPU, CPU).
"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from loguru import logger

from fileorg.llm_classifier.ports.interfaces import ILLMProvider


class OnnxProvider(ILLMProvider):
    """
    ONNX Runtime implementation of ILLMProvider.

    Provides fast, lightweight inference using pre-exported ONNX models.
    Supports multiple hardware acceleration platforms with automatic fallback.

    Benefits over torch-based providers:
        - No torch/transformers dependencies at runtime
        - Faster startup time (~5-10x faster)
        - Smaller installation size (~2GB vs ~10GB)
        - Cross-platform hardware acceleration
        - Production-ready deployment
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        model_path: Optional[str] = None,
        tokenizer_path: Optional[str] = None,
        execution_provider: Optional[str] = None,
        max_new_tokens: int = 2048,
        **session_options,
    ):
        """
        Initialize ONNX provider.

        Args:
            model_name: Model name (e.g., "Llama-3.2-3B-Instruct")
                       If None, uses default
            model_path: Explicit path to ONNX model directory or file
                       If None, uses models/{model_name}/
            tokenizer_path: Path to tokenizer.json
                           If None, uses models/{model_name}/tokenizer.json
            execution_provider: Explicit provider ('cuda', 'coreml', 'qnn', 'cpu', or None for auto)
            max_new_tokens: Maximum number of new tokens to generate (default: 2048)
            **session_options: Additional ONNX Runtime session options
        """
        # Default model name
        if model_name is None:
            model_name = "Llama-3.2-3B-Instruct"

        self.model_name = model_name
        models_base_dir = Path(__file__).parent.parent.parent / "models"

        # Set model directory
        if model_path is None:
            # Use model-specific subdirectory
            self.model_dir = models_base_dir / model_name
        else:
            model_path_obj = Path(model_path)
            if model_path_obj.is_dir():
                self.model_dir = model_path_obj
            else:
                # If path is a file, use its parent directory
                self.model_dir = model_path_obj.parent

        # Find ONNX model file in directory
        # Optimum typically creates decoder_model.onnx or decoder_model_merged.onnx
        onnx_files = list(self.model_dir.glob("*.onnx")) if self.model_dir.exists() else []
        if onnx_files:
            # Prefer merged model if available (single file inference)
            self.model_path = next((f for f in onnx_files if "merged" in f.name.lower()), onnx_files[0])
        else:
            # Fallback path (will error on load if not exists)
            self.model_path = self.model_dir / "decoder_model.onnx"

        # Set tokenizer path
        if tokenizer_path is None:
            self.tokenizer_path = self.model_dir / "tokenizer.json"
        else:
            self.tokenizer_path = Path(tokenizer_path)

        self.max_new_tokens = max_new_tokens
        self.session_options = session_options

        # Lazy loading
        self._session = None
        self._tokenizer = None
        self._execution_providers = None

        # Auto-detect or set execution provider
        self.requested_provider = execution_provider
        self._setup_execution_providers()

        logger.info(f"Initialized OnnxProvider with model={self.model_path.name}, providers={self._execution_providers}")

    def _setup_execution_providers(self):
        """Configure execution providers based on available hardware."""
        try:
            import onnxruntime as ort

            available = ort.get_available_providers()

            if self.requested_provider:
                # Explicit provider requested
                provider_map = {
                    "cuda": "CUDAExecutionProvider",
                    "coreml": "CoreMLExecutionProvider",
                    "qnn": "QNNExecutionProvider",
                    "cpu": "CPUExecutionProvider",
                }

                requested = provider_map.get(self.requested_provider.lower())
                if requested and requested in available:
                    self._execution_providers = [requested, "CPUExecutionProvider"]
                else:
                    logger.warning(
                        f"Requested provider '{self.requested_provider}' not available. Available: {available}. Falling back to auto-detection."
                    )
                    self._execution_providers = self._auto_detect_providers(available)
            else:
                # Auto-detect
                self._execution_providers = self._auto_detect_providers(available)

        except ImportError:
            logger.warning("ONNX Runtime not installed. Provider setup skipped.")
            self._execution_providers = []

    def _auto_detect_providers(self, available: List[str]) -> List[str]:
        """
        Auto-detect best execution providers.

        Priority:
            1. CUDA (NVIDIA GPU)
            2. CoreML (Apple Silicon)
            3. QNN (Qualcomm NPU)
            4. CPU (fallback)
        """
        providers = []

        # Priority order
        priority = [
            "CUDAExecutionProvider",
            "CoreMLExecutionProvider",
            "QNNExecutionProvider",
        ]

        for provider in priority:
            if provider in available:
                providers.append(provider)
                break  # Use first available accelerator

        # Always add CPU as fallback
        providers.append("CPUExecutionProvider")

        return providers

    def _load_session(self):
        """Lazy load ONNX Runtime session."""
        if self._session is not None:
            return

        try:
            import onnxruntime as ort

            # Check if model exists
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"ONNX model not found at {self.model_path}. "
                    f"Please run 'fileorg-export-llm' to export the model first.\n\n"
                    f"Quick start:\n"
                    f"  1. Install export dependencies: pip install -e '.[llm-export]'\n"
                    f"  2. Export model: fileorg-export-llm\n"
                    f"  3. Run again with ONNX acceleration"
                )

            logger.info(f"Loading ONNX model from {self.model_path}...")

            # Configure provider options
            provider_options = self._get_provider_options()

            # Create session options
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            # Enable profiling for debugging (optional)
            # sess_options.enable_profiling = True

            # Apply custom session options
            for key, value in self.session_options.items():
                setattr(sess_options, key, value)

            # Create inference session
            if provider_options:
                self._session = ort.InferenceSession(
                    str(self.model_path),
                    sess_options=sess_options,
                    providers=self._execution_providers,
                    provider_options=provider_options,
                )
            else:
                self._session = ort.InferenceSession(
                    str(self.model_path),
                    sess_options=sess_options,
                    providers=self._execution_providers,
                )

            # Log active providers
            active_providers = self._session.get_providers()
            logger.success(f"ONNX model loaded successfully. Active providers: {active_providers}")

            # Warn if using CPU only
            if active_providers == ["CPUExecutionProvider"]:
                logger.warning(
                    "Using CPU-only inference. For better performance:\n"
                    "  - NVIDIA GPU: Install onnxruntime-gpu\n"
                    "  - Apple Silicon: CoreML should be available by default\n"
                    "  - Qualcomm NPU: Install QNN execution provider"
                )

        except ImportError as e:
            logger.error("onnxruntime not installed. Install with: pip install onnxruntime-gpu")
            raise ImportError(
                "ONNX Runtime required for OnnxProvider. Install with: pip install onnxruntime-gpu (or onnxruntime for CPU-only)"
            ) from e
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")
            raise

    def _get_provider_options(self) -> List[Dict]:
        """Get provider-specific options."""
        options = []

        for provider in self._execution_providers:
            if provider == "CUDAExecutionProvider":
                options.append(
                    {
                        "device_id": 0,
                        "arena_extend_strategy": "kNextPowerOfTwo",
                        "gpu_mem_limit": 8 * 1024 * 1024 * 1024,  # 8GB
                        "cudnn_conv_algo_search": "EXHAUSTIVE",
                        "do_copy_in_default_stream": True,
                    }
                )
            elif provider == "CoreMLExecutionProvider":
                options.append(
                    {
                        "MLComputeUnits": 0,  # 0 = All, 1 = CPU only, 2 = CPU and GPU
                    }
                )
            elif provider == "QNNExecutionProvider":
                options.append(
                    {
                        # QNN-specific options
                        # TODO: Add QNN configuration
                    }
                )
            else:
                options.append({})

        return options

    def _load_tokenizer(self):
        """Lazy load tokenizer."""
        if self._tokenizer is not None:
            return

        try:
            from tokenizers import Tokenizer

            # Check if tokenizer exists
            if not self.tokenizer_path.exists():
                raise FileNotFoundError(
                    f"Tokenizer not found at {self.tokenizer_path}. Please run 'fileorg-export-llm' to export the tokenizer first."
                )

            logger.info(f"Loading tokenizer from {self.tokenizer_path}...")
            self._tokenizer = Tokenizer.from_file(str(self.tokenizer_path))

            # Configure tokenizer
            if self._tokenizer.padding is None:
                # Add padding if not configured
                self._tokenizer.enable_padding(pad_id=0, pad_token="<pad>")  # nosec B106

            logger.success("Tokenizer loaded successfully")

        except ImportError as e:
            logger.error("tokenizers library not installed. Install with: pip install tokenizers")
            raise ImportError("tokenizers library required for OnnxProvider. Install with: pip install tokenizers") from e
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise

    def _format_chat_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Format chat messages into Llama 3.2 chat template format.

        Args:
            messages: Chat format messages [{"role": "user/system", "content": "..."}]

        Returns:
            Formatted prompt string
        """
        formatted = "<|begin_of_text|>"

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                formatted += f"<|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "user":
                formatted += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "assistant":
                formatted += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"

        # Add generation prompt
        formatted += "<|start_header_id|>assistant<|end_header_id|>\n\n"

        return formatted

    def generate(self, messages: List[Dict[str, str]], max_tokens: int = 32768) -> str:
        """
        Generate text using ONNX Runtime with autoregressive decoding.

        Args:
            messages: Chat format messages [{"role": "user/system", "content": "..."}]
            max_tokens: Maximum input tokens (for truncation)

        Returns:
            Generated text string

        Raises:
            RuntimeError: If inference errors occur
        """
        self._load_session()
        self._load_tokenizer()

        try:
            # Format messages
            formatted_prompt = self._format_chat_messages(messages)
            logger.debug(f"Formatted prompt length: {len(formatted_prompt)} chars")

            # Tokenize
            encoding = self._tokenizer.encode(formatted_prompt)
            input_ids = encoding.ids

            # Truncate if needed
            if len(input_ids) > max_tokens:
                logger.warning(f"Input truncated from {len(input_ids)} to {max_tokens} tokens")
                input_ids = input_ids[:max_tokens]

            # Convert to numpy
            input_ids_array = np.array([input_ids], dtype=np.int64)
            attention_mask = np.ones_like(input_ids_array, dtype=np.int64)

            logger.debug(f"Running ONNX inference (input tokens: {len(input_ids)})...")

            # Autoregressive generation
            generated_ids = self._generate_autoregressive(input_ids_array, attention_mask, max_new_tokens=self.max_new_tokens)

            # Decode (skip input tokens, only decode generated part)
            generated_text = self._tokenizer.decode(generated_ids[len(input_ids) :], skip_special_tokens=True)

            logger.debug(f"Generated {len(generated_ids) - len(input_ids)} tokens ({len(generated_text)} chars)")

            return generated_text

        except Exception as e:
            logger.error(f"ONNX inference failed: {e}")
            raise RuntimeError(f"ONNX inference failed: {e}") from e

    def _generate_autoregressive(self, input_ids: np.ndarray, attention_mask: np.ndarray, max_new_tokens: int = 2048) -> List[int]:
        """
        Autoregressive generation loop.

        Args:
            input_ids: Input token IDs (batch_size, seq_len)
            attention_mask: Attention mask (batch_size, seq_len)
            max_new_tokens: Maximum number of new tokens to generate

        Returns:
            Complete token sequence (input + generated)
        """
        # Special token IDs (Llama 3.2)
        EOS_TOKEN_ID = 128009  # <|eot_id|>

        # Get input names from model
        input_names = [inp.name for inp in self._session.get_inputs()]

        # Start with input tokens
        current_ids = input_ids[0].tolist()  # Convert to list for easy appending

        # Generation loop
        for _ in range(max_new_tokens):
            # Prepare current input
            current_input_ids = np.array([current_ids], dtype=np.int64)
            current_attention_mask = np.ones_like(current_input_ids, dtype=np.int64)

            # Prepare ONNX inputs
            ort_inputs = {input_names[0]: current_input_ids}

            # Add attention mask if model expects it
            if len(input_names) > 1 and "attention_mask" in input_names[1].lower():
                ort_inputs[input_names[1]] = current_attention_mask

            # Run inference
            outputs = self._session.run(None, ort_inputs)

            # Get logits (assume first output)
            logits = outputs[0]  # Shape: (batch_size, seq_len, vocab_size)

            # Get next token (greedy decoding - argmax of last token)
            next_token_logits = logits[0, -1, :]
            next_token_id = int(np.argmax(next_token_logits))

            # Check for EOS
            if next_token_id == EOS_TOKEN_ID:
                break

            # Append to sequence
            current_ids.append(next_token_id)

        return current_ids

    def is_available(self) -> bool:
        """Check if the provider is available."""
        try:
            self._load_session()
            self._load_tokenizer()
            return True
        except Exception as e:
            logger.debug(f"OnnxProvider not available: {e}")
            return False

    def get_device_info(self) -> Dict[str, any]:
        """Get device information for debugging."""
        try:
            import onnxruntime as ort

            available_providers = ort.get_available_providers()
        except ImportError:
            available_providers = []

        info = {
            "provider_type": "onnx",
            "execution_providers": self._execution_providers,
            "model_path": str(self.model_path),
            "tokenizer_path": str(self.tokenizer_path),
            "model_exists": self.model_path.exists(),
            "tokenizer_exists": self.tokenizer_path.exists(),
            "available_providers": available_providers,
            "max_new_tokens": self.max_new_tokens,
        }

        if self._session:
            info["active_providers"] = self._session.get_providers()

        return info
