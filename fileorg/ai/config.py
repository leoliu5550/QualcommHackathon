"""
Unified Configuration Module for FileOrg System

Provides centralized configuration for both LLM backend and prompt engineering settings.
Supports presets and runtime configuration updates.
"""

from typing import Any, Dict, Optional

# Core LLM Configuration
LLM_CONFIG = {
    "backend": "local",  # Options: "local", "qualcomm"
    "model_id": "iFaz/llama32_3B_en_emo_2000_stp",
    # "dlc_path": "tinyllama.dlc",  # For Qualcomm backend
    # "tokenizer_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
}

# Prompt Engineering Configuration
PROMPT_CONFIG = {
    # Classifier Version Control
    "classifier_version": "v2",  # Options: "v1" (legacy), "v2" (enhanced with prompt engineering)
    "enable_v2_features": True,  # Global switch for v2 features
    
    # Version Control
    "prompt_version": "v2",  # Options: "v1" (legacy), "v2" (enhanced)
    "use_advanced_prompt": True,
    
    # Few-shot Learning
    "use_few_shot": True,  # Enabled for better accuracy
    "few_shot_count": 2,
    
    # Domain Detection
    "use_domain_detection": False,  # Can be enabled for specialized classification
    "domain_keywords_threshold": 2,
    
    # Content Optimization
    "optimize_content": False,
    "max_content_length": 500,
    
    # Output Validation
    "validate_output": False,
    "strict_json": False,
    
    # Model Optimization Parameters
    "temperature": 0.1,
    "top_p": 0.95,
    "repetition_penalty": 1.0,
    "max_new_tokens": 200
}

# Preset Configurations
PRESETS = {
    "legacy": {
        "prompt_version": "v1",
        "use_advanced_prompt": False,
        "use_few_shot": False,
        "use_domain_detection": False
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


class Config:
    """Configuration manager with preset support and runtime updates."""
    
    def __init__(self, preset: Optional[str] = None):
        """Initialize configuration with optional preset.
        
        Args:
            preset: Name of preset to load ("legacy", "balanced", "advanced")
        """
        self._llm_config = LLM_CONFIG.copy()
        self._prompt_config = PROMPT_CONFIG.copy()
        
        if preset:
            self.load_preset(preset)
    
    def load_preset(self, preset_name: str = "legacy") -> "Config":
        """Load a configuration preset.
        
        Args:
            preset_name: Name of the preset to load
            
        Returns:
            Self for method chaining
        """
        if preset_name in PRESETS:
            self._prompt_config.update(PRESETS[preset_name])
        return self
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # Check LLM config first, then prompt config
        if key in self._llm_config:
            return self._llm_config[key]
        elif key in self._prompt_config:
            return self._prompt_config[key]
        return default
    
    def update(self, **kwargs) -> "Config":
        """Update configuration values.
        
        Args:
            **kwargs: Key-value pairs to update
            
        Returns:
            Self for method chaining
        """
        for key, value in kwargs.items():
            if key in self._llm_config:
                self._llm_config[key] = value
            elif key in self._prompt_config:
                self._prompt_config[key] = value
            else:
                # Add to prompt config if new key
                self._prompt_config[key] = value
        return self
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values combined.
        
        Returns:
            Combined dictionary of all configurations
        """
        return {**self._llm_config, **self._prompt_config}
    
    @property
    def llm(self) -> Dict[str, Any]:
        """Get LLM configuration.
        
        Returns:
            LLM configuration dictionary
        """
        return self._llm_config
    
    @property
    def prompt(self) -> Dict[str, Any]:
        """Get prompt configuration.
        
        Returns:
            Prompt configuration dictionary
        """
        return self._prompt_config
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"Config(backend={self.get('backend')}, prompt_version={self.get('prompt_version')})"


# Default instance for backward compatibility
# This maintains compatibility with existing code that imports 'config' directly
_default_config = Config()
config = _default_config.llm  # Backward compatible with original mode_config.py


# Convenience functions for quick access
def get_config(preset: Optional[str] = None) -> Config:
    """Get a new configuration instance with optional preset.
    
    Args:
        preset: Preset name to load
        
    Returns:
        New Config instance
    """
    return Config(preset=preset)


def update_default_config(**kwargs):
    """Update the default configuration instance.
    
    Args:
        **kwargs: Configuration values to update
    """
    global config
    _default_config.update(**kwargs)
    config = _default_config.llm  # Keep backward compatibility