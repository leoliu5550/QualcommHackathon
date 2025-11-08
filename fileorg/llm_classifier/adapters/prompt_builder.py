"""
Prompt builder adapter for LLM-based file classification.

This module provides a concrete implementation of the IPromptBuilder interface,
constructing chat-formatted prompts for file classification tasks with support
for batch processing, suggested categories, and bilingual instructions.
"""

import json
from typing import Dict, List, Optional

from fileorg.llm_classifier.ports import IPromptBuilder


class BasicPromptBuilder(IPromptBuilder):
    """
    Basic prompt builder for LLM-based file classification.

    Constructs bilingual (Chinese/English) prompts that instruct the LLM to
    categorize files based on their content and metadata. Supports batch
    processing of multiple files and optional suggested categories to improve
    classification accuracy.

    Usage:
        builder = BasicPromptBuilder(suggested_categories=["Documents", "Images"])
        messages = builder.build_prompt(
            text='{"file1.txt": {"path": "/path/to/file1.txt", "content": "..."}}',
            instruction="Classify these files into meaningful categories"
        )
        response = llm_provider.generate(messages)
    """

    def __init__(self, suggested_categories: Optional[List[str]] = None):
        """
        Initialize prompt builder with optional suggested categories.

        Args:
            suggested_categories: Optional list of category names to suggest to the LLM.
                                 The LLM can still create new categories dynamically.
                                 Examples: ["Documents", "Images", "Code", "Data"]
        """
        self.suggested_categories = suggested_categories or []

    def build_prompt(self, text: str, instruction: str, max_tokens: int = 150000) -> List[Dict[str, str]]:
        """
        Build classification prompt from file data and instruction.

        Args:
            text: JSON-formatted string containing file data. Expected structure:
                  {
                      "filename1": {"path": "...", "content": "..."},
                      "filename2": {"path": "...", "content": "..."},
                      ...
                  }
            instruction: Classification instruction in natural language.
                        Example: "Classify these files into meaningful categories"
            max_tokens: Maximum tokens for input text. Text will be truncated if exceeded.

        Returns:
            Chat-formatted messages for LLM consumption:
            [
                {"role": "system", "content": "<system prompt>"},
                {"role": "user", "content": "<instruction + file data>"}
            ]

        Raises:
            ValueError: If text is not valid JSON format
        """
        # First validate that input is valid JSON
        try:
            file_data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Input text must be valid JSON format: {e}") from e

        # Truncate text to respect token limit (rough approximation: 1 token ≈ 4 characters)
        max_chars = max_tokens * 4
        if len(text) > max_chars:
            # Try to truncate gracefully by removing files from the data structure
            truncated_data = {}
            current_size = 2  # Account for opening and closing braces
            for filename, metadata in file_data.items():
                # Estimate size of this entry
                entry_json = json.dumps({filename: metadata})
                entry_size = len(entry_json) + 2  # +2 for comma and space
                if current_size + entry_size <= max_chars:
                    truncated_data[filename] = metadata
                    current_size += entry_size
                else:
                    break
            final_text = json.dumps(truncated_data, ensure_ascii=False)
        else:
            final_text = text

        # Build system prompt with bilingual instructions
        system_content = self._build_system_prompt()

        # Build user prompt with instruction and file data
        user_content = self._build_user_prompt(instruction, final_text)

        messages = [{"role": "system", "content": system_content}, {"role": "user", "content": user_content}]

        return messages

    def _build_system_prompt(self) -> str:
        """
        Build bilingual system prompt with classification guidelines.

        Returns:
            System prompt string with Chinese and English instructions
        """
        base_prompt = (
            "You are an intelligent file organization assistant. "
            "Analyze the provided file contents and metadata, then categorize them into "
            "meaningful, descriptive categories based on their content, purpose, and context.\n\n"
            "你是一個智能文件整理助手。"
            "分析提供的文件內容和元數據，然後根據內容、用途和上下文將它們分類到有意義且描述性的類別中。\n\n"
            "Requirements / 要求:\n"
            "1. Create clear and descriptive category names / 創建清晰且描述性的類別名稱\n"
            "2. Group similar files together / 將相似的文件分組在一起\n"
            "3. Consider file content, name, and extension / 考慮文件內容、名稱和副檔名\n"
        )

        # Add suggested categories if provided
        if self.suggested_categories:
            categories_str = ", ".join(self.suggested_categories)
            base_prompt += (
                f"4. You may reference these suggested categories, but can create new ones if needed / "
                f"你可以參考這些建議類別，但如果需要也可以創建新類別:\n"
                f"   {categories_str}\n"
            )
        else:
            base_prompt += "4. Create categories dynamically based on file content / 根據文件內容動態創建類別\n"

        # Add output format requirements
        base_prompt += (
            "\n"
            "Output Format / 輸出格式:\n"
            "Respond ONLY with valid JSON in this exact format:\n"
            "僅以以下 JSON 格式回應:\n"
            '{\n  "Category Name": ["file1.txt", "file2.pdf"],\n  "Another Category": ["file3.docx"]\n}\n'
            "\n"
            "Example / 範例:\n"
            "{\n"
            '  "Statistics": ["analysis.pdf", "data.csv"],\n'
            '  "Documents": ["report.docx", "notes.txt"],\n'
            '  "Web Content": ["article.html"]\n'
            "}"
        )

        return base_prompt

    def _build_user_prompt(self, instruction: str, file_data: str) -> str:
        """
        Build user prompt combining instruction and file data.

        Args:
            instruction: User-provided classification instruction
            file_data: JSON-formatted file data

        Returns:
            Formatted user prompt string
        """
        user_prompt = f"{instruction}\n\nFiles to classify / 待分類文件:\n```json\n{file_data}\n```"

        return user_prompt
