"""
TURU LLM Provider Implementation.

This module provides a TURU API-based LLM provider using httpx for local API calls.
TURU runs models locally via HTTP API endpoints.
"""

from typing import Dict, List

import httpx
from loguru import logger

from fileorg.llm_classifier.ports.interfaces import ILLMProvider


class TURUProvider(ILLMProvider):
    """
    TURU LLM provider using local HTTP API.

    TURU provides a local API server for running LLM models with OpenAI-compatible endpoints.

    Features:
        - Local API calls via httpx
        - OpenAI-compatible chat completions API
        - Configurable timeout for long-running inferences
        - Support for custom model selection

    Usage:
        provider = TURUProvider(
            api_key="your_api_key",
            base_url="http://127.0.0.1:80/v1.0",
            model=".bot/Llama 3.1 8B @NPU",
            temperature=0.1
        )
        response = provider.generate(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=32768
        )

    Thread-safety: Safe for concurrent use if httpx.Client is not shared.
    """

    def __init__(
        self,
        api_key: str = "API_KEY",
        base_url: str = "http://127.0.0.1:80/v1.0",
        model: str = ".bot/Llama 3.1 8B @NPU",
        temperature: float = 0.1,
        timeout: float = 600.0,
    ):
        """
        Initialize TURU provider with API configuration.

        Args:
            api_key: API key for authentication (default: "API_KEY")
            base_url: Base URL for TURU API (default: "http://127.0.0.1:80/v1.0")
            model: Model identifier (default: ".bot/Llama 3.1 8B @NPU")
            temperature: Sampling temperature (default: 0.1 for more deterministic output)
            timeout: Request timeout in seconds (default: 600.0 for 10 minutes)

        Note:
            The base_url should include the API version (e.g., "/v1")
            Port and version are configurable via the base_url parameter.
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")  # Remove trailing slash
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

        logger.info(f"Initialized TURUProvider with model={model}, base_url={base_url}, timeout={timeout}s")

    def generate(self, messages: List[Dict[str, str]], max_tokens: int = 32768) -> str:
        """
        Generate text using TURU API.

        Args:
            messages: Chat-formatted messages
                     Example: [{"role": "user", "content": "Hello"}]
            max_tokens: Maximum tokens to generate (not enforced by TURU, for compatibility)

        Returns:
            Generated text string from the last message

        Raises:
            RuntimeError: If API request fails or returns invalid response
            httpx.TimeoutException: If request exceeds timeout
            httpx.HTTPError: For other HTTP-related errors

        Note:
            This method extracts the content from the last message in the response choices.
        """
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

        try:
            logger.debug(f"Calling TURU API at {url} with {len(messages)} messages")

            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)

            # Raise exception for HTTP errors (4xx, 5xx)
            response.raise_for_status()

            # Parse response
            response_data = response.json()

            # Extract generated text from response
            if "choices" not in response_data or not response_data["choices"]:
                raise RuntimeError("Invalid API response: missing 'choices' field")

            # Get the last choice's message content
            llm_response = response_data["choices"][-1]["message"]["content"]

            logger.success(f"TURU API response received: {len(llm_response)} characters")
            return llm_response

        except httpx.TimeoutException as e:
            logger.error(f"TURU API request timed out after {self.timeout}s")
            raise RuntimeError(f"TURU API timeout after {self.timeout}s: {e}") from e

        except httpx.HTTPStatusError as e:
            logger.error(f"TURU API HTTP error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"TURU API HTTP error: {e.response.status_code}") from e

        except httpx.HTTPError as e:
            logger.error(f"TURU API request failed: {e}")
            raise RuntimeError(f"TURU API request failed: {e}") from e

        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Failed to parse TURU API response: {e}")
            raise RuntimeError(f"Invalid TURU API response format: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error during TURU API call: {e}")
            raise RuntimeError(f"TURU API call failed: {e}") from e

    def get_device_info(self) -> str:
        """
        Get device information.

        Returns:
            Device info string (always returns "TURU API" for this provider)
        """
        return f"TURU API (model: {self.model}, endpoint: {self.base_url})"
