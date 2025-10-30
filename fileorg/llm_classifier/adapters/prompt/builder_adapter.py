"""
Prompt Builder Adapter

This adapter implements PromptBuilderPort by wrapping existing prompt building logic.

SOLID Principles:
    - Single Responsibility: Only handles prompt construction
    - Liskov Substitution: Can replace any PromptBuilderPort implementation
    - Dependency Inversion: Implements the abstract PromptBuilderPort
"""

from typing import List, Dict
from fileorg.llm_classifier.ports import PromptBuilderPort
from fileorg.llm_classifier.adapters.prompt._templates import PromptTemplates
from fileorg.llm_classifier.adapters.prompt._examples import FewShotExamples


class PromptBuilderAdapter(PromptBuilderPort):
    """
    Adapter for prompt building using templates and examples.

    Constructs optimized prompts for classification and remapping tasks
    with support for multiple versions, few-shot learning, and domain detection.

    Attributes:
        version: Prompt template version ('v1' or 'v2')
        use_few_shot: Whether to include few-shot examples
        use_domain_detection: Whether to detect and use domain hints
        templates: Template manager instance
        examples: Example manager instance
    """

    def __init__(
        self,
        version: str = "v2",
        use_few_shot: bool = True,
        use_domain_detection: bool = False
    ):
        """
        Initialize prompt builder adapter.

        Args:
            version: Prompt template version ('v1' or 'v2')
            use_few_shot: Enable few-shot learning examples
            use_domain_detection: Enable automatic domain detection
        """
        self.version = version
        self.use_few_shot = use_few_shot
        self.use_domain_detection = use_domain_detection
        self.templates = PromptTemplates()
        self.examples = FewShotExamples()

    def build_classification_prompt(
        self,
        content: str,
        max_length: int = 500
    ) -> List[Dict[str, str]]:
        """
        Build optimized classification prompt.

        Args:
            content: Document content to classify
            max_length: Maximum content length to include

        Returns:
            List of message dictionaries for LLM inference
        """
        # Truncate content if needed
        truncated_content = content[:max_length] if len(content) > max_length else content

        # Get appropriate template
        template = self.templates.get_template(self.version, "classification")

        # Build messages based on version
        if self.version == "v1":
            # Legacy format
            messages = [
                {
                    "role": "system",
                    "content": template["system"]
                },
                {
                    "role": "user",
                    "content": template["prompt_prefix"] + truncated_content
                },
                {
                    "role": "assistant",
                    "content": template["assistant_prefix"]
                }
            ]
        else:
            # Enhanced v2 format
            messages = [
                {
                    "role": "system",
                    "content": template["system"]
                }
            ]

            # Add few-shot examples if enabled
            if self.use_few_shot:
                relevant_examples = self.examples.get_relevant_examples(
                    truncated_content,
                    count=2
                )
                for ex in relevant_examples:
                    messages.append({
                        "role": "user",
                        "content": f"Classify this: {ex['input'][:200]}"
                    })
                    messages.append({
                        "role": "assistant",
                        "content": ex['output']
                    })

            # Add domain hint if detected
            domain_hint = ""
            if self.use_domain_detection:
                detected_domain = self.templates.detect_domain(truncated_content)
                if detected_domain != "General":
                    domain_hint = f"\nHint: This appears to be {detected_domain}-related content.\n"

            # Add actual content to classify
            messages.append({
                "role": "user",
                "content": template["prompt_prefix"] + domain_hint + truncated_content
            })
            messages.append({
                "role": "assistant",
                "content": template["assistant_prefix"]
            })

        return messages

    def build_remapping_prompt(
        self,
        folder_names: List[str]
    ) -> List[Dict[str, str]]:
        """
        Build prompt for folder name grouping.

        Args:
            folder_names: List of folder names to group

        Returns:
            List of message dictionaries for LLM inference
        """
        template = self.templates.get_template(self.version, "remapping")

        if self.version == "v1":
            # Legacy format
            folder_list = "[" + ", ".join(folder_names) + "]"
            messages = [
                {
                    "role": "system",
                    "content": 'you are a master of categorizing folder names and give it a new group name in json format, eg. {"foldername":"/foldername", "groupname":"/groupname"]}'
                },
                {
                    "role": "user",
                    "content": "categorize the foldername into several groups if they are related or similar and give each group a name, must in json format:" + folder_list
                },
                {
                    "role": "assistant",
                    "content": '{"groups": ["'
                }
            ]
        else:
            # Enhanced v2 format
            messages = [
                {
                    "role": "system",
                    "content": template["system"]
                }
            ]

            # Add examples if enabled
            if self.use_few_shot:
                examples = self.examples.get_examples("remapping", count=2)
                for ex in examples:
                    messages.append({
                        "role": "user",
                        "content": f"Group these folders: {ex['input']}"
                    })
                    messages.append({
                        "role": "assistant",
                        "content": str(ex['output'])
                    })

            # Add actual folders to group
            messages.append({
                "role": "user",
                "content": template["prompt_prefix"] + str(folder_names)
            })
            messages.append({
                "role": "assistant",
                "content": template["assistant_prefix"]
            })

        return messages
