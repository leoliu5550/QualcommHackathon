"""
Jinja2 Prompt Builder Adapter

This adapter implements IPromptBuilderPort using Jinja2 templates for prompt engineering.
All prompts are stored as .jinja2 template files, ensuring no hard-coded prompts in Python code.

SOLID Principles:
    - Single Responsibility: Only handles prompt rendering via Jinja2
    - Open/Closed: Open for extension via new templates
    - Liskov Substitution: Can replace any IPromptBuilderPort implementation
    - Dependency Inversion: Implements the abstract IPromptBuilderPort
"""

import json
from typing import List, Dict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

from fileorg.llm_classifier.ports import IPromptBuilderPort


class Jinja2PromptAdapter(IPromptBuilderPort):
    """
    Adapter for prompt building using Jinja2 templates.

    Loads prompt templates from the templates/ directory and renders them
    with dynamic variables. Supports multiple template versions and formats.

    Attributes:
        env: Jinja2 environment for template loading
        templates_dir: Path to templates directory
        version: Default template version to use
    """

    def __init__(
        self,
        templates_dir: str | None = None,
        version: str = "v2"
    ):
        """
        Initialize Jinja2 prompt adapter.

        Args:
            templates_dir: Directory containing .jinja2 template files
                          (defaults to fileorg/llm_classifier/templates/)
            version: Default prompt template version ('v1' or 'v2')
        """
        if templates_dir is None:
            # Auto-detect templates directory relative to this file
            current_file = Path(__file__)
            templates_dir = current_file.parent.parent.parent / "templates"

        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            raise ValueError(
                f"Templates directory not found: {self.templates_dir}. "
                f"Please ensure the templates/ directory exists with .jinja2 files."
            )

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False  # We're not rendering HTML
        )

        self.version = version

    def build_classification_prompt(
        self,
        content: str,
        max_length: int = 500
    ) -> List[Dict[str, str]]:
        """
        Build optimized classification prompt using Jinja2 template.

        Args:
            content: Document content to classify
            max_length: Maximum content length to include

        Returns:
            List of message dictionaries for LLM inference

        Raises:
            FileNotFoundError: If classification.jinja2 template not found
        """
        template = self.env.get_template("classification.jinja2")

        # Render template with variables
        rendered = template.render(
            content=content,
            max_length=max_length,
            version=self.version
        )

        # Parse the JSON output from template
        try:
            messages = json.loads(rendered)
            return messages
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse template output as JSON. "
                f"Template may have syntax errors: {e}"
            )

    def build_remapping_prompt(
        self,
        folder_names: List[str]
    ) -> List[Dict[str, str]]:
        """
        Build prompt for folder name grouping using Jinja2 template.

        Args:
            folder_names: List of folder names to group

        Returns:
            List of message dictionaries for LLM inference

        Raises:
            FileNotFoundError: If remapping.jinja2 template not found
        """
        template = self.env.get_template("remapping.jinja2")

        # Render template with variables
        rendered = template.render(
            folder_names=folder_names,
            version=self.version
        )

        # Parse the JSON output from template
        try:
            messages = json.loads(rendered)
            return messages
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse template output as JSON. "
                f"Template may have syntax errors: {e}"
            )

    def set_version(self, version: str) -> None:
        """
        Change the template version at runtime.

        Args:
            version: Template version to use ('v1' or 'v2')
        """
        if version not in ["v1", "v2"]:
            raise ValueError(f"Invalid template version: {version}. Must be 'v1' or 'v2'.")
        self.version = version

    def render_custom_template(
        self,
        template_name: str,
        **kwargs
    ) -> List[Dict[str, str]]:
        """
        Render a custom template with arbitrary variables.

        This method allows for flexibility in rendering additional templates
        beyond the standard classification and remapping templates.

        Args:
            template_name: Name of the template file (e.g., 'my_template.jinja2')
            **kwargs: Variables to pass to the template

        Returns:
            List of message dictionaries for LLM inference

        Raises:
            FileNotFoundError: If template not found
        """
        template = self.env.get_template(template_name)
        rendered = template.render(**kwargs)

        try:
            messages = json.loads(rendered)
            return messages
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse template output as JSON: {e}"
            )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Jinja2PromptAdapter(templates_dir={self.templates_dir}, "
            f"version={self.version})"
        )


# Convenience function
def create_jinja_prompt_builder(
    templates_dir: str | None = None,
    version: str = "v2"
) -> Jinja2PromptAdapter:
    """
    Create a Jinja2 prompt builder instance.

    Args:
        templates_dir: Custom templates directory (optional)
        version: Template version to use

    Returns:
        Jinja2PromptAdapter instance
    """
    return Jinja2PromptAdapter(templates_dir=templates_dir, version=version)
