"""
Qualcomm LLM Adapter

This adapter implements the LLMPort interface for Qualcomm Snapdragon NPU inference.
It provides NPU-accelerated inference with power-efficient processing.

SOLID Principles:
    - Single Responsibility: Only handles Qualcomm NPU communication
    - Open/Closed: Closed for modification, open for extension via subclassing
    - Liskov Substitution: Can replace any LLMPort implementation
    - Dependency Inversion: Implements the abstract LLMPort
"""

import os
from typing import List, Dict
import httpx
from fileorg.llm_classifier.ports import LLMPort


class QualcommLLMAdapter(LLMPort):
    """
    Adapter for Qualcomm Snapdragon NPU-accelerated inference.

    This adapter leverages Qualcomm AI Hub API for edge AI inference on
    Snapdragon devices, providing high performance with low power consumption.

    Attributes:
        api_key: Authentication token for API access
        api_url: Endpoint URL for NPU inference API
        model: Model identifier for NPU deployment
        timeout: HTTP request timeout in seconds
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str = "http://127.0.0.1:80/v1.0/chat/completions",
        model: str = ".bot/Llama 3.1 8B @NPU",
        timeout: float = 600.0
    ):
        """
        Initialize Qualcomm NPU adapter.

        Args:
            api_key: API authentication key (or from QUALCOMM_API_KEY env var)
            api_url: NPU inference API endpoint
            model: Model identifier for NPU
            timeout: HTTP request timeout in seconds

        Raises:
            ValueError: If API key is not provided
        """
        self.api_key = api_key or os.getenv("QUALCOMM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Qualcomm API key must be provided via 'api_key' parameter "
                "or 'QUALCOMM_API_KEY' environment variable"
            )

        self.api_url = api_url
        self.model = model
        self.timeout = timeout

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 200
    ) -> str:
        """
        Generate text using Qualcomm NPU-accelerated inference.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            max_tokens: Maximum tokens to generate (not used by current API)

        Returns:
            Generated text response from the model

        Raises:
            httpx.HTTPError: If API request fails
            KeyError: If API response format is unexpected
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()

        response_data = response.json()
        return response_data["choices"][-1]["message"]["content"]
