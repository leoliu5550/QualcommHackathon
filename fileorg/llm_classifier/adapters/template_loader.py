"""
Template loader adapter for Jinja2-based prompt management.

This module provides a concrete implementation of the ITemplateLoader interface,
enabling version-controlled, provider-specific prompt templates with efficient
caching and filesystem-based storage.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple

import jinja2

from fileorg.llm_classifier.ports.interfaces import ITemplateLoader


class Jinja2TemplateLoader(ITemplateLoader):
    """
    Filesystem-based Jinja2 template loader with LRU caching.

    Features:
        - In-memory caching for performance (templates loaded once)
        - Helpful error messages with available providers
        - Jinja2 environment configured for text prompts (not HTML)
        - Template validation at load time

    Usage:
        # Standalone usage
        loader = Jinja2TemplateLoader(base_path="prompts/")
        system_tmpl = loader.load_template("llama3b", "v1", "system")
        content = system_tmpl.render(suggested_categories=["Docs", "Code"])

        # Composed with prompt builder (recommended)
        loader = Jinja2TemplateLoader(base_path="prompts/")
        builder = LlamaPromptBuilder(template_loader=loader, provider="llama3b")

    Thread-safety: Not thread-safe due to cache. Use separate instances
    in multi-threaded environments or add locking.
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize template loader.

        Args:
            base_path: Base directory for templates. Defaults to
                      "prompts/" relative to this module's directory.
                      Can be absolute or relative path.
        """
        if base_path is None:
            # Default: prompts/ directory next to this file
            module_dir = Path(__file__).parent.parent
            self.base_path = module_dir / "prompts"
        else:
            self.base_path = Path(base_path)

        # Cache: (provider, version, template_type) -> jinja2.Template
        self._template_cache: Dict[Tuple[str, str, str], jinja2.Template] = {}

        # Jinja2 environment with autoescape disabled (for raw text prompts)
        # We're generating LLM prompts (text), not HTML. Templates are not user-controlled
        # and contain no web content, so autoescape=False is safe for this use case.
        self._jinja_env = jinja2.Environment(  # nosec B701
            loader=jinja2.FileSystemLoader(str(self.base_path)),
            autoescape=False,  # Prompts are text, not HTML
            trim_blocks=True,  # Remove first newline after template tag
            lstrip_blocks=True,  # Strip leading whitespace before template tags
        )

    def load_template(self, provider: str, version: str, template_type: str) -> jinja2.Template:
        """
        Load a specific template with caching.

        Args:
            provider: LLM provider name (e.g., "llama3b", "llama8b")
            version: Template version (e.g., "v1", "v2")
            template_type: Type of template (e.g., "system", "user")

        Returns:
            Jinja2 Template object ready for rendering

        Raises:
            FileNotFoundError: If template file doesn't exist
            jinja2.TemplateError: If template syntax is invalid
        """
        cache_key = (provider, version, template_type)

        # Return cached template if available
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        # Construct template path: {provider}/{version}/{template_type}.jinja2
        template_path = f"{provider}/{version}/{template_type}.jinja2"

        # Check if file exists
        full_path = self.base_path / template_path
        if not full_path.exists():
            raise FileNotFoundError(
                f"Template not found: {template_path}\nExpected location: {full_path}\nAvailable providers: {self._list_providers()}"
            )

        # Load template using Jinja2 environment
        try:
            template = self._jinja_env.get_template(template_path)
        except jinja2.TemplateError as e:
            raise ValueError(f"Invalid template syntax in {template_path}: {e}") from e

        # Cache and return
        self._template_cache[cache_key] = template
        return template

    def template_exists(self, provider: str, version: str, template_type: str) -> bool:
        """
        Check if a template exists without loading it.

        Args:
            provider: LLM provider name
            version: Template version
            template_type: Type of template

        Returns:
            True if template file exists, False otherwise
        """
        template_path = self.base_path / provider / version / f"{template_type}.jinja2"
        return template_path.exists()

    def clear_cache(self) -> None:
        """
        Clear the template cache.

        Useful for testing or when templates are modified at runtime.
        """
        self._template_cache.clear()

    def _list_providers(self) -> list[str]:
        """
        List available provider directories.

        Returns:
            List of provider names found in base_path
        """
        if not self.base_path.exists():
            return []

        return [d.name for d in self.base_path.iterdir() if d.is_dir()]
