"""
Classification prompt builder adapter for Stage 2 file classification.

This module provides prompt builders for classifying files based on
their keywords extracted in Stage 1.
"""

import json
from typing import Dict, List

from fileorg.llm_classifier.ports.interfaces import IPromptBuilder, ITemplateLoader


class ClassificationPromptBuilder(IPromptBuilder):
    """
    Prompt builder for Stage 2 file classification based on keywords.

    Generates prompts that instruct the LLM to classify files into categories
    based on the keywords extracted from Stage 1.

    Llama Chat Format:
        Constructs prompts using the official Llama 3 chat template format:
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>

        {system_content}<|eot_id|><|start_header_id|>user<|end_header_id|>

        {user_content}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

    Usage:
        loader = Jinja2TemplateLoader(base_path="prompts/")
        builder = ClassificationPromptBuilder(
            template_loader=loader,
            provider="llama3b",
            version="v2"
        )
        # file_summaries = {"path1": "keyword1", "path2": "keyword2"}
        messages = builder.build_prompt(
            text='{"path1": "keyword1"}',
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
    ):
        """
        Initialize Classification prompt builder.

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
        if not template_loader.template_exists(provider, version, "classification_system"):
            raise FileNotFoundError(f"Classification system template not found for {provider}/{version}")
        if not template_loader.template_exists(provider, version, "classification_user"):
            raise FileNotFoundError(f"Classification user template not found for {provider}/{version}")

    def build_prompt(self, text: str, instruction: str, max_tokens: int = 150000) -> List[Dict[str, str]]:
        """
        Build Llama-formatted prompt for file classification.

        Args:
            text: JSON-formatted string containing file summaries. Expected structure:
                  {
                      "file_path1": "keyword1",
                      "file_path2": "keyword2",
                      ...
                  }
            instruction: Classification instruction in natural language
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
            file_summaries = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Input text must be valid JSON format: {e}") from e

        # Truncate text to respect token limit (rough approximation: 1 token ≈ 4 characters)
        truncated_text = self._truncate_text(text, file_summaries, max_tokens)

        # Load templates
        system_template = self.template_loader.load_template(self.provider, self.version, "classification_system")
        user_template = self.template_loader.load_template(self.provider, self.version, "classification_user")

        # Render templates with context
        system_content = system_template.render()
        user_content = user_template.render(instruction=instruction, file_summaries=truncated_text)

        # Construct Llama chat format
        formatted_prompt = self._format_llama_chat(system_content, user_content)

        # Return as single message (Llama processes the special tokens internally)
        return [{"role": "user", "content": formatted_prompt}]

    def _truncate_text(self, text: str, file_summaries: dict, max_tokens: int) -> str:
        """
        Truncate text to respect token limit.

        Args:
            text: Original JSON text
            file_summaries: Parsed file summaries dictionary
            max_tokens: Maximum token count

        Returns:
            Truncated JSON string
        """
        max_chars = max_tokens * 4

        if len(text) <= max_chars:
            return text

        # Gracefully truncate by removing files from the data structure
        truncated_data = {}
        current_size = 2  # Account for opening and closing braces

        for file_path, keyword in file_summaries.items():
            entry_json = json.dumps({file_path: keyword})
            entry_size = len(entry_json) + 2  # +2 for comma and space

            if current_size + entry_size <= max_chars:
                truncated_data[file_path] = keyword
                current_size += entry_size
            else:
                break

        return json.dumps(truncated_data, ensure_ascii=False)

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
