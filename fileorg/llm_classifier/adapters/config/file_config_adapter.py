"""
File-based Configuration Adapter

This adapter implements the ConfigPort interface using dataclasses for configuration
management with support for presets and runtime updates.

SOLID Principles:
    - Single Responsibility: Only handles configuration management
    - Liskov Substitution: Can replace any ConfigPort implementation
    - Dependency Inversion: Implements the abstract ConfigPort
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field, replace, asdict
from fileorg.llm_classifier.ports import ConfigPort


# ============================================================================
# Configuration Data Classes
# ============================================================================

@dataclass
class LLMConfig:
    """LLM backend configuration."""
    backend: str = "qualcomm"
    model_id: str = "iFaz/llama32_3B_en_emo_2000_stp"
    api_key: Optional[str] = None
    api_url: str = "http://127.0.0.1:80/v1.0/chat/completions"
    model: str = ".bot/Llama 3.1 8B @NPU"
    timeout: float = 600.0
    device: str = "cuda"
    cache_dir: str = "./fileorg/llm_classifier/llm/model"


@dataclass
class PromptConfig:
    """Prompt engineering configuration."""
    classifier_version: str = "v2"
    enable_v2_features: bool = True
    prompt_version: str = "v2"
    use_advanced_prompt: bool = True
    use_few_shot: bool = True
    few_shot_count: int = 2
    use_domain_detection: bool = False
    domain_keywords_threshold: int = 2
    optimize_content: bool = False
    max_content_length: int = 500
    validate_output: bool = False
    strict_json: bool = False
    temperature: float = 0.1
    top_p: float = 0.95
    repetition_penalty: float = 1.0
    max_new_tokens: int = 200


# ============================================================================
# Preset Configurations
# ============================================================================

PRESETS = {
    "legacy": {
        "prompt_version": "v1",
        "use_advanced_prompt": False,
        "use_few_shot": False,
        "use_domain_detection": False,
        "classifier_version": "v1"
    },
    "balanced": {
        "classifier_version": "v2",
        "prompt_version": "v2",
        "use_advanced_prompt": True,
        "use_few_shot": True,
        "use_domain_detection": False,
        "few_shot_count": 2
    },
    "advanced": {
        "classifier_version": "v2",
        "prompt_version": "v2",
        "use_advanced_prompt": True,
        "use_few_shot": True,
        "use_domain_detection": True,
        "few_shot_count": 3,
        "optimize_content": True,
        "validate_output": True
    }
}


# ============================================================================
# Config Adapter Implementation
# ============================================================================

class FileConfigAdapter(ConfigPort):
    """
    File-based configuration adapter.

    Manages LLM and prompt configurations with support for presets
    and runtime updates. Uses dataclasses for type safety and validation.

    Attributes:
        _llm_config: LLM backend configuration
        _prompt_config: Prompt engineering configuration
    """

    def __init__(self, preset: Optional[str] = None, **kwargs):
        """
        Initialize configuration adapter.

        Args:
            preset: Preset name to load ('legacy', 'balanced', 'advanced')
            **kwargs: Additional configuration overrides
        """
        self._llm_config = LLMConfig()
        self._prompt_config = PromptConfig()

        if preset:
            self.load_preset(preset)

        if kwargs:
            self.update(**kwargs)

    def load_preset(self, preset_name: str) -> None:
        """
        Load a configuration preset.

        Args:
            preset_name: Name of preset to load

        Raises:
            ValueError: If preset is not recognized
        """
        if preset_name not in PRESETS:
            raise ValueError(
                f"Unknown preset: {preset_name}. "
                f"Available presets: {', '.join(PRESETS.keys())}"
            )

        preset_values = PRESETS[preset_name]
        self.update(**preset_values)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Searches in LLM config first, then prompt config.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if hasattr(self._llm_config, key):
            return getattr(self._llm_config, key)
        elif hasattr(self._prompt_config, key):
            return getattr(self._prompt_config, key)
        return default

    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get LLM configuration as dictionary.

        Returns:
            Dictionary of LLM configuration values
        """
        return asdict(self._llm_config)

    def get_prompt_config(self) -> Dict[str, Any]:
        """
        Get prompt configuration as dictionary.

        Returns:
            Dictionary of prompt configuration values
        """
        return asdict(self._prompt_config)

    def update(self, **kwargs) -> None:
        """
        Update configuration values.

        Values are automatically routed to appropriate configuration.

        Args:
            **kwargs: Key-value pairs to update
        """
        llm_updates = {}
        prompt_updates = {}

        for key, value in kwargs.items():
            if hasattr(self._llm_config, key):
                llm_updates[key] = value
            elif hasattr(self._prompt_config, key):
                prompt_updates[key] = value

        if llm_updates:
            self._llm_config = replace(self._llm_config, **llm_updates)
        if prompt_updates:
            self._prompt_config = replace(self._prompt_config, **prompt_updates)

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values combined.

        Returns:
            Combined dictionary of all configurations
        """
        return {**asdict(self._llm_config), **asdict(self._prompt_config)}

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"FileConfigAdapter(backend={self.get('backend')}, "
            f"prompt_version={self.get('prompt_version')}, "
            f"classifier_version={self.get('classifier_version')})"
        )


# ============================================================================
# Convenience Functions
# ============================================================================

def get_config(preset: Optional[str] = None, **kwargs) -> FileConfigAdapter:
    """
    Create a configuration adapter instance.

    Args:
        preset: Preset name to load
        **kwargs: Additional configuration overrides

    Returns:
        Configuration adapter instance
    """
    return FileConfigAdapter(preset=preset, **kwargs)
