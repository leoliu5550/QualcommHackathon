"""
Summary prompt builder adapter for Stage 1 keyword extraction.

This module provides prompt builders for extracting 1-2 word keywords
from individual file contents using Llama model family.
"""

import json
from typing import Dict, List

from fileorg.llm_classifier.ports.interfaces import IPromptBuilder, ITemplateLoader


class SummaryPromptBuilder(IPromptBuilder):
    """
    Prompt builder for Stage 1 keyword extraction from file contents.

    Generates prompts that instruct the LLM to extract 1-2 word keywords
    that best describe the file content.

    Llama Chat Format:
        Constructs prompts using the official Llama 3 chat template format:
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>

        {system_content}<|eot_id|><|start_header_id|>user<|end_header_id|>

        {user_content}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

    Usage:
        loader = Jinja2TemplateLoader(base_path="prompts/")
        builder = SummaryPromptBuilder(
            template_loader=loader,
            provider="llama3b",
            version="v2"
        )
        messages = builder.build_prompt(
            text='{"file.txt": "content..."}',
            instruction="Extract keyword"
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
    ):
        """
        Initialize Summary prompt builder.

        Args:
            template_loader: Template loader implementing ITemplateLoader
            provider: Provider name matching template directory (e.g., "llama3b", "llama8b")
            version: Template version to use (e.g., "v1")

        Raises:
            FileNotFoundError: If templates for provider/version don't exist
        """
        self.template_loader = template_loader
        self.provider = provider
        self.version = version

        # Validate that templates exist at initialization
        if not template_loader.template_exists(provider, version, "summary_system"):
            raise FileNotFoundError(f"Summary system template not found for {provider}/{version}")
        if not template_loader.template_exists(provider, version, "summary_user"):
            raise FileNotFoundError(f"Summary user template not found for {provider}/{version}")

    def build_prompt(self, text: str, instruction: str, max_tokens: int = 150000) -> List[Dict[str, str]]:
        """
        Build Llama-formatted prompt for keyword extraction.

        Args:
            text: JSON-formatted string containing single file data. Expected structure:
                  {
                      "file_path": "file content..."
                  }
            instruction: Keyword extraction instruction in natural language
            max_tokens: Maximum tokens for input text. Text will be truncated if exceeded.

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
            json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Input text must be valid JSON format: {e}") from e

        # Truncate text to respect token limit (rough approximation: 1 token ≈ 4 characters)
        truncated_text = self._truncate_text(text, max_tokens)

        # Load templates
        system_template = self.template_loader.load_template(self.provider, self.version, "summary_system")
        user_template = self.template_loader.load_template(self.provider, self.version, "summary_user")

        # Render templates with context
        system_content = system_template.render()
        user_content = user_template.render(instruction=instruction, file_data=truncated_text)

        # Construct Llama chat format
        formatted_prompt = self._format_llama_chat(system_content, user_content)

        # Return as single message (Llama processes the special tokens internally)
        return [{"role": "user", "content": formatted_prompt}]

    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to respect token limit.

        Args:
            text: Original JSON text
            max_tokens: Maximum token count

        Returns:
            Truncated JSON string
        """
        max_chars = max_tokens * 4

        if len(text) <= max_chars:
            return text

        # Truncate content while preserving JSON structure
        try:
            file_data = json.loads(text)
            for file_path, content in file_data.items():
                if isinstance(content, str):
                    # Truncate the content string
                    truncated_content = content[:max_chars]
                    file_data[file_path] = truncated_content
                    break  # Only process the first file

            return json.dumps(file_data, ensure_ascii=False)
        except Exception:
            # Fallback to simple truncation
            return text[:max_chars]

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
