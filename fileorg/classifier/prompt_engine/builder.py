"""Prompt Builder Module for Advanced LLM Prompting.

This module provides sophisticated prompt construction capabilities for
improved LLM classification and grouping tasks.
"""

from typing import List, Dict
from .templates import PromptTemplates
from .examples import FewShotExamples


class PromptBuilder:
    """Constructs optimized prompts based on content and configuration.
    
    This class builds sophisticated prompts for LLM inference, supporting
    multiple template versions, few-shot learning, and domain-specific
    optimizations.
    
    Attributes:
        version (str): Prompt template version ('v1' or 'v2').
        use_few_shot (bool): Whether to include few-shot examples.
        use_domain_detection (bool): Whether to detect and use domain hints.
        templates: Instance of PromptTemplates for template management.
        examples: Instance of FewShotExamples for example selection.
    """
    
    def __init__(self, version: str = "v2", use_few_shot: bool = True, use_domain_detection: bool = True):
        """Initialize the PromptBuilder with specified configuration.
        
        Args:
            version (str): Prompt template version. 'v1' for legacy compatibility,
                'v2' for enhanced templates with better classification guidance.
                Defaults to 'v2'.
            use_few_shot (bool): Include relevant few-shot examples in prompts
                to improve LLM understanding and accuracy. Defaults to True.
            use_domain_detection (bool): Automatically detect content domain
                (academic, business, technology, etc.) and include domain hints
                in prompts. Defaults to True.
        """
        self.version = version
        self.use_few_shot = use_few_shot
        self.use_domain_detection = use_domain_detection
        self.templates = PromptTemplates()
        self.examples = FewShotExamples()
    
    def build_classification_prompt(self, content: str, max_content_length: int = 500) -> List[Dict[str, str]]:
        """Build an optimized classification prompt for the given content.
        
        Constructs a prompt that guides the LLM to classify content into
        appropriate folder categories. Supports both legacy and enhanced
        prompt formats.
        
        Args:
            content (str): The text content to classify. Can be full document
                or excerpt.
            max_content_length (int): Maximum characters to include from content.
                Content is intelligently truncated if needed. Defaults to 500.
            
        Returns:
            List[Dict[str, str]]: List of message dictionaries formatted for
                LLM inference. Each dict contains 'role' and 'content' keys.
        
        Example:
            >>> builder = PromptBuilder(version="v2")
            >>> prompt = builder.build_classification_prompt("Statistics chapter...")
            >>> # Returns messages ready for LLM inference
        """
        # Truncate content if needed
        truncated_content = content[:max_content_length] if len(content) > max_content_length else content
        
        # Get appropriate template
        template = self.templates.get_template(self.version, "classification")
        
        # Build messages based on version
        if self.version == "v1":
            # Legacy format for backward compatibility
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
                relevant_examples = self.examples.get_relevant_examples(truncated_content, count=2)
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
    
    def build_remapping_prompt(self, folder_names: List[str]) -> List[Dict[str, str]]:
        """Build a prompt for grouping related folder names.
        
        Constructs a prompt that guides the LLM to intelligently group
        similar or related folder names to reduce redundancy.
        
        Args:
            folder_names (List[str]): List of folder names to analyze and group.
                Example: ["Statistics", "Mathematics", "DataAnalysis"]
            
        Returns:
            List[Dict[str, str]]: List of message dictionaries formatted for
                LLM inference, guiding it to output folder-to-group mappings.
        
        Example:
            >>> builder = PromptBuilder()
            >>> folders = ["Statistics", "Mathematics", "Orders"]
            >>> prompt = builder.build_remapping_prompt(folders)
            >>> # LLM will group Statistics & Mathematics together
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
    
    def build_custom_prompt(self, content: str, task: str = "classify", **kwargs) -> List[Dict[str, str]]:
        """Build a custom prompt for specialized tasks.
        
        Provides flexibility to create prompts for various task types
        beyond standard classification and grouping.
        
        Args:
            content (str): Input content or data for the task.
            task (str): Type of task. Supported values:
                - 'classify': Document classification
                - 'group' or 'remap': Folder name grouping
                - Other values: Returns simple prompt
                Defaults to 'classify'.
            **kwargs: Additional task-specific parameters passed to the
                appropriate prompt builder method.
            
        Returns:
            List[Dict[str, str]]: List of message dictionaries for LLM inference.
        """
        if task == "classify":
            return self.build_classification_prompt(content, **kwargs)
        elif task == "group" or task == "remap":
            return self.build_remapping_prompt(content, **kwargs)
        else:
            # Fallback to simple prompt
            return [
                {
                    "role": "user",
                    "content": content
                }
            ]
    
    def optimize_for_model(self, messages: List[Dict], model_name: str = "llama") -> List[Dict]:
        """Optimize prompts for specific model architectures.
        
        Adjusts prompt formatting and structure based on known characteristics
        of different LLM models for optimal performance.
        
        Args:
            messages (List[Dict]): Original message list to optimize.
            model_name (str): Target model name for optimization.
                Currently supports: 'llama', 'gpt', 'claude'.
                Defaults to 'llama'.
            
        Returns:
            List[Dict]: Optimized messages tailored for the specified model.
        
        Note:
            This method is a placeholder for future model-specific optimizations.
            Currently returns messages unchanged.
        """
        # Model-specific optimizations can be added here
        # For now, return as-is
        return messages