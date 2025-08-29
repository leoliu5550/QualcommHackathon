"""Unified Configuration Module for FileOrg System."""

from typing import Any, Dict, Optional

# Core LLM Configuration
LLM_CONFIG = {
    "backend": "qualcomm",  # Options: "local", "qualcomm"
    "model_id": "iFaz/llama32_3B_en_emo_2000_stp",
    # "dlc_path": "tinyllama.dlc",  # For Qualcomm backend
    # "tokenizer_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
}

# Prompt Engineering Configuration
PROMPT_CONFIG = {
    "prompt_version": "v2",  # Options: "v1" (legacy), "v2" (enhanced)
    "use_few_shot": True,
    "use_domain_detection": False,
}



class Config:
    """Configuration manager with preset support and runtime updates."""
    
    def __init__(self):
        """Initialize configuration."""
        self._llm_config = LLM_CONFIG.copy()
        self._prompt_config = PROMPT_CONFIG.copy()
    
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
    


# Default instance for backward compatibility
_default_config = Config()
config = _default_config.llm  # Backward compatible with existing imports


def update_default_config(**kwargs):
    """Update the default configuration instance.
    
    Args:
        **kwargs: Configuration values to update
    """
    global config
    _default_config.update(**kwargs)
    config = _default_config.llm  # Keep backward compatibility