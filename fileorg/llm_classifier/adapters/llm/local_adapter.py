"""
Local Transformers LLM Adapter

This adapter implements the LLMPort interface for local transformer-based inference
using Hugging Face transformers library with GPU/CPU support.

SOLID Principles:
    - Single Responsibility: Only handles local transformer inference
    - Liskov Substitution: Can replace any LLMPort implementation
    - Dependency Inversion: Implements the abstract LLMPort
"""

from typing import List, Dict
from fileorg.llm_classifier.ports import LLMPort


class LocalTransformersAdapter(LLMPort):
    """
    Adapter for local transformer-based LLM inference.

    Uses Hugging Face transformers library for GPU/CPU inference with
    automatic device detection and graceful fallback.

    Attributes:
        device: Computing device ('cuda' or 'cpu')
        model: Loaded transformer model
        tokenizer: Associated tokenizer
        llm: Text generation pipeline
    """

    def __init__(
        self,
        model_id: str,
        device: str = "cuda",
        cache_dir: str = "./fileorg/llm_classifier/llm/model"
    ):
        """
        Initialize local transformer adapter.

        Args:
            model_id: Hugging Face model identifier
            device: Preferred device ('cuda' or 'cpu')
            cache_dir: Directory for caching models

        Note:
            Automatically falls back to CPU if CUDA is unavailable.
        """
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        # Check CUDA availability and fall back to CPU if needed
        if device == "cuda" and not torch.cuda.is_available():
            self.device = "cpu"
            print("CUDA not available, falling back to CPU")
        else:
            self.device = device

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            cache_dir=cache_dir
        )

        # Load model with graceful handling of quantization
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                cache_dir=cache_dir
            ).to(self.device)
        except (ImportError, Exception) as e:
            error_str = str(e)
            if any(keyword in error_str for keyword in ["bitsandbytes", "quantization", "No package metadata"]):
                print("Loading model without quantization (bitsandbytes not available)")
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    cache_dir=cache_dir,
                    quantization_config=None,
                    load_in_4bit=False,
                    load_in_8bit=False
                ).to(self.device)
            else:
                raise

        self.llm = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            return_full_text=False
        )

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 200
    ) -> str:
        """
        Generate text using local transformer model.

        Args:
            messages: List of message dictionaries (converted to text prompt)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Note:
            Converts message format to plain text for the model.
        """
        # Convert messages to plain text prompt
        prompt = self._messages_to_text(messages)

        output = self.llm(
            prompt,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=0.1
        )[0]["generated_text"]

        return output

    def _messages_to_text(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert message list to plain text prompt.

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted text prompt
        """
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n\n".join(prompt_parts)
