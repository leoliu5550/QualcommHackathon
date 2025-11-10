"""
Llama-specific prompt builder adapter using Jinja2 templates.

This module provides prompt builders for Llama model family (3B, 8B, etc.)
with proper chat template formatting and version-controlled templates.
"""

import json
from typing import Dict, List, Optional

from fileorg.llm_classifier.ports import IPromptBuilder, ITemplateLoader


class LlamaPromptBuilder(IPromptBuilder):
    """
    Prompt builder for Llama model family with Jinja2 template support.

    Llama Chat Format:
        Constructs prompts using the official Llama 3 chat template format:
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>

        {system_content}<|eot_id|><|start_header_id|>user<|end_header_id|>

        {user_content}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

    Version Control:
        Supports version-controlled templates (v1, v2, etc.) for:
        - A/B testing different prompt strategies
        - Gradual rollout of improvements
        - Model-specific optimizations (llama3b vs llama8b)

    Usage:
        loader = Jinja2TemplateLoader(base_path="prompts/")
        builder = LlamaPromptBuilder(
            template_loader=loader,
            provider="llama3b",
            version="v1",
            suggested_categories=["Documents", "Code"]
        )
        messages = builder.build_prompt(
            text='{"file.txt": {"path": "/path", "content": "..."}}',
            instruction="Classify files"
        )

    Thread-safety: Safe if template_loader is thread-safe or not shared.
    """

    # Llama 3 special tokens
    BEGIN_OF_TEXT = "<|begin_of_text|>"
    START_HEADER = "<|start_header_id|>"
    END_HEADER = "<|end_header_id|>"
    EOT = "<|eot_id|>"

    def __init__(
        self,
        template_loader: ITemplateLoader,
        provider: str = "llama3b",
        version: str = "v1",
        suggested_categories: Optional[List[str]] = None,
    ):
        """
        Initialize Llama prompt builder.

        Args:
            template_loader: Template loader implementing ITemplateLoader
            provider: Provider name matching template directory (e.g., "llama3b", "llama8b")
            version: Template version to use (e.g., "v1", "v2")
            suggested_categories: Optional category suggestions to pass to templates

        Raises:
            FileNotFoundError: If templates for provider/version don't exist
        """
        self.template_loader = template_loader
        self.provider = provider
        self.version = version
        self.suggested_categories = suggested_categories or []

        # Validate that templates exist at initialization
        if not template_loader.template_exists(provider, version, "system"):
            raise FileNotFoundError(f"System template not found for {provider}/{version}")
        if not template_loader.template_exists(provider, version, "user"):
            raise FileNotFoundError(f"User template not found for {provider}/{version}")

    def build_prompt(
        self, text: str, instruction: str, max_tokens: int = 150000, suggested_categories: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Build Llama-formatted prompt from file data and instruction.

        Args:
            text: JSON-formatted string containing file data. Expected structure:
                  {
                      "/path/to/file1.txt": "content of file 1",
                      "/path/to/file2.pdf": "content of file 2",
                      ...
                  }
            instruction: Classification instruction in natural language
            max_tokens: Maximum tokens for input text. Text will be truncated if exceeded.
            suggested_categories: Optional list of category names to suggest to LLM.
                                 If None, uses categories from initialization.
                                 If provided, overrides initialization categories.

        Returns:
            Single-element list with complete Llama-formatted prompt:
            [
                {
                    "role": "user",
                    "content": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n
                               {system_prompt}<|eot_id|>..."
                }
            ]

        Raises:
            ValueError: If text is not valid JSON format
            jinja2.TemplateError: If template rendering fails

        Note:
            Unlike standard chat format (separate system/user messages),
            Llama requires everything in a single formatted string.
        """
        # Validate and parse JSON input
        try:
            file_data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Input text must be valid JSON format: {e}") from e

        # Truncate text to respect token limit (rough approximation: 1 token ≈ 4 characters)
        truncated_data = self._truncate_files(file_data, max_tokens)

        # Load templates
        system_template = self.template_loader.load_template(self.provider, self.version, "system")
        user_template = self.template_loader.load_template(self.provider, self.version, "user")

        # Use provided categories or fall back to initialization categories
        categories = suggested_categories if suggested_categories is not None else self.suggested_categories

        # Render templates with context
        system_content = system_template.render(suggested_categories=categories)
        user_content = user_template.render(instruction=instruction, files=truncated_data)

        # Construct Llama chat format
        formatted_prompt = self._format_llama_chat(system_content, user_content)

        # Return as single message (Llama processes the special tokens internally)
        return [{"role": "user", "content": formatted_prompt}]

    def _truncate_files(self, file_data: dict, max_tokens: int) -> dict:
        """
        Truncate file data to respect token limit.

        Args:
            file_data: Parsed file data dictionary
            max_tokens: Maximum token count

        Returns:
            Truncated file data dictionary
        """
        max_chars = max_tokens * 4

        # Calculate current size
        current_json = json.dumps(file_data, ensure_ascii=False)

        if len(current_json) <= max_chars:
            return file_data

        # Gracefully truncate by removing files from the data structure
        truncated_data = {}
        current_size = 2  # Account for opening and closing braces

        for filename, metadata in file_data.items():
            entry_json = json.dumps({filename: metadata})
            entry_size = len(entry_json) + 2  # +2 for comma and space

            if current_size + entry_size <= max_chars:
                truncated_data[filename] = metadata
                current_size += entry_size
            else:
                break

        return truncated_data

    def _format_llama_chat(self, system_content: str, user_content: str) -> str:
        """
        Format content into Llama 3 chat template.

        Args:
            system_content: Rendered system prompt
            user_content: Rendered user prompt

        Returns:
            Formatted string with Llama special tokens
        """
        # Llama 3 chat template format
        formatted = (
            f"{self.BEGIN_OF_TEXT}"
            f"{self.START_HEADER}system{self.END_HEADER}\n\n"
            f"{system_content}{self.EOT}"
            f"{self.START_HEADER}user{self.END_HEADER}\n\n"
            f"{user_content}{self.EOT}"
            f"{self.START_HEADER}assistant{self.END_HEADER}\n\n"
        )

        return formatted
