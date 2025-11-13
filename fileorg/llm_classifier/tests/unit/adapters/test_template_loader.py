"""
Unit tests for Jinja2TemplateLoader adapter.

Tests verify that Jinja2TemplateLoader correctly implements the ITemplateLoader
interface and properly loads, caches, and manages Jinja2 templates from the filesystem.
"""

import jinja2
import pytest

from fileorg.llm_classifier.adapters.template_loader import Jinja2TemplateLoader
from fileorg.llm_classifier.ports import ITemplateLoader


@pytest.fixture
def temp_template_dir(tmp_path):
    """Create a temporary template directory structure for testing."""
    # Create llama3b/v1 templates
    llama3b_v1 = tmp_path / "llama3b" / "v1"
    llama3b_v1.mkdir(parents=True)
    (llama3b_v1 / "system.jinja2").write_text("System prompt for {{ model }}")
    (llama3b_v1 / "user.jinja2").write_text("User: {{ message }}")

    # Create llama8b/v1 templates
    llama8b_v1 = tmp_path / "llama8b" / "v1"
    llama8b_v1.mkdir(parents=True)
    (llama8b_v1 / "system.jinja2").write_text("Enhanced system prompt for {{ model }}")
    (llama8b_v1 / "user.jinja2").write_text("User input: {{ message }}")

    # Create llama3b/v2 templates
    llama3b_v2 = tmp_path / "llama3b" / "v2"
    llama3b_v2.mkdir(parents=True)
    (llama3b_v2 / "system.jinja2").write_text("V2 system prompt for {{ model }}")

    return tmp_path


@pytest.fixture
def loader(temp_template_dir):
    """Provide a template loader with temporary template directory."""
    return Jinja2TemplateLoader(base_path=temp_template_dir)


class TestJinja2TemplateLoaderInterface:
    """Test that Jinja2TemplateLoader correctly implements ITemplateLoader interface."""

    def test_implements_interface(self, loader):
        """Verify Jinja2TemplateLoader implements ITemplateLoader."""
        assert isinstance(loader, ITemplateLoader)

    def test_has_load_template_method(self, loader):
        """Verify load_template method exists and is callable."""
        assert hasattr(loader, "load_template")
        assert callable(loader.load_template)

    def test_has_template_exists_method(self, loader):
        """Verify template_exists method exists and is callable."""
        assert hasattr(loader, "template_exists")
        assert callable(loader.template_exists)


class TestTemplateLoading:
    """Test template loading functionality."""

    def test_load_existing_template(self, loader):
        """Should successfully load an existing template."""
        template = loader.load_template("llama3b", "v1", "system")
        assert template is not None
        assert isinstance(template, jinja2.Template)

    def test_load_template_with_different_providers(self, loader):
        """Should load templates from different provider directories."""
        llama3b_template = loader.load_template("llama3b", "v1", "system")
        llama8b_template = loader.load_template("llama8b", "v1", "system")

        # Templates should be different
        assert llama3b_template.render(model="test") != llama8b_template.render(model="test")

    def test_load_template_with_different_versions(self, loader):
        """Should load templates from different version directories."""
        v1_template = loader.load_template("llama3b", "v1", "system")
        v2_template = loader.load_template("llama3b", "v2", "system")

        # Templates should be different
        assert v1_template.render(model="test") != v2_template.render(model="test")

    def test_load_different_template_types(self, loader):
        """Should load different template types (system, user, etc.)."""
        system_template = loader.load_template("llama3b", "v1", "system")
        user_template = loader.load_template("llama3b", "v1", "user")

        # Templates should be different
        rendered_system = system_template.render(model="test")
        rendered_user = user_template.render(message="test")
        assert rendered_system != rendered_user

    def test_load_nonexistent_template(self, loader):
        """Should raise FileNotFoundError for nonexistent template."""
        with pytest.raises(FileNotFoundError, match="Template not found"):
            loader.load_template("nonexistent", "v1", "system")

    def test_load_nonexistent_version(self, loader):
        """Should raise FileNotFoundError for nonexistent version."""
        with pytest.raises(FileNotFoundError, match="Template not found"):
            loader.load_template("llama3b", "v99", "system")

    def test_load_nonexistent_template_type(self, loader):
        """Should raise FileNotFoundError for nonexistent template type."""
        with pytest.raises(FileNotFoundError, match="Template not found"):
            loader.load_template("llama3b", "v1", "nonexistent")


class TestTemplateRendering:
    """Test that loaded templates can be rendered correctly."""

    def test_render_template_with_context(self, loader):
        """Should render template with provided context."""
        template = loader.load_template("llama3b", "v1", "system")
        rendered = template.render(model="Llama-3B")
        assert "Llama-3B" in rendered

    def test_render_user_template(self, loader):
        """Should render user template with message."""
        template = loader.load_template("llama3b", "v1", "user")
        rendered = template.render(message="Hello world")
        assert "Hello world" in rendered


class TestTemplateCaching:
    """Test template caching behavior."""

    def test_template_cached_after_first_load(self, loader):
        """Should cache template after first load."""
        template1 = loader.load_template("llama3b", "v1", "system")
        template2 = loader.load_template("llama3b", "v1", "system")

        # Should return the same cached object
        assert template1 is template2

    def test_different_templates_cached_separately(self, loader):
        """Should cache different templates separately."""
        system_template = loader.load_template("llama3b", "v1", "system")
        user_template = loader.load_template("llama3b", "v1", "user")

        # Should be different objects
        assert system_template is not user_template

    def test_clear_cache(self, loader):
        """Should clear cache when requested."""
        # Load template twice without clearing cache
        loader.load_template("llama3b", "v1", "system")
        cache_size_before = len(loader._template_cache)

        # Clear cache
        loader.clear_cache()
        cache_size_after = len(loader._template_cache)

        # Cache should be empty after clearing
        assert cache_size_before > 0
        assert cache_size_after == 0


class TestTemplateExistence:
    """Test template_exists functionality."""

    def test_existing_template_returns_true(self, loader):
        """Should return True for existing template."""
        assert loader.template_exists("llama3b", "v1", "system") is True

    def test_nonexistent_template_returns_false(self, loader):
        """Should return False for nonexistent template."""
        assert loader.template_exists("nonexistent", "v1", "system") is False

    def test_nonexistent_version_returns_false(self, loader):
        """Should return False for nonexistent version."""
        assert loader.template_exists("llama3b", "v99", "system") is False

    def test_nonexistent_type_returns_false(self, loader):
        """Should return False for nonexistent template type."""
        assert loader.template_exists("llama3b", "v1", "nonexistent") is False


class TestPathHandling:
    """Test path handling and directory structure."""

    def test_default_base_path(self):
        """Should use default base path when none provided."""
        loader = Jinja2TemplateLoader()
        assert loader.base_path is not None
        assert "prompts" in str(loader.base_path)

    def test_custom_base_path(self, temp_template_dir):
        """Should use custom base path when provided."""
        loader = Jinja2TemplateLoader(base_path=temp_template_dir)
        assert loader.base_path == temp_template_dir

    def test_relative_base_path(self, temp_template_dir):
        """Should handle relative base paths."""
        loader = Jinja2TemplateLoader(base_path=temp_template_dir)
        assert loader.base_path.exists()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_template_syntax(self, tmp_path):
        """Should raise ValueError for invalid Jinja2 syntax."""
        # Create template with invalid syntax
        provider_dir = tmp_path / "test_provider" / "v1"
        provider_dir.mkdir(parents=True)
        (provider_dir / "system.jinja2").write_text("Invalid {{ syntax")

        loader = Jinja2TemplateLoader(base_path=tmp_path)

        with pytest.raises(ValueError, match="Invalid template syntax"):
            loader.load_template("test_provider", "v1", "system")

    def test_empty_template(self, tmp_path):
        """Should handle empty template files."""
        provider_dir = tmp_path / "test_provider" / "v1"
        provider_dir.mkdir(parents=True)
        (provider_dir / "system.jinja2").write_text("")

        loader = Jinja2TemplateLoader(base_path=tmp_path)
        template = loader.load_template("test_provider", "v1", "system")

        assert template.render() == ""
