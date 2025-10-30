"""
LLM Classifier Module - Hexagonal Architecture

This module provides a unified interface for LLM-based document classification
following hexagonal architecture principles with clean separation of concerns.

Architecture:
    📄 ports.py
       └─ All port definitions (Inbound & Outbound interfaces)

    📁 adapters/ (Infrastructure Layer)
       ├─ llm/ - LLM backend adapters (Qualcomm NPU, Local Transformers)
       ├─ config/ - Configuration management
       ├─ prompt/ - Prompt engineering (templates, validation)
       └─ persistence/ - Data storage (JSON)

    📄 run.py
       └─ Application services & dependency injection

Example Usage:
    # New Architecture (Recommended)
    from fileorg.llm_classifier import create_classifier_system, run_classification

    classifier, remapper, processor = create_classifier_system()
    result = run_classification(summaries_data, base_output_dir="./organized")

    # Backward Compatibility
    from fileorg.llm_classifier import get_classifier

    classifier = get_classifier()
    folder_name = classifier.create_folder_name("document content")

For detailed architecture documentation, see ARCHITECTURE.md
"""

# New Hexagonal Architecture Exports
from fileorg.llm_classifier.run import (
    create_classifier_system,
    run_classification,
    DocumentClassificationService,
    FolderRemappingService,
    FileProcessingService,
    CreateFolderNamer  # Backward compatibility wrapper
)

# Legacy Exports (for backward compatibility)
from fileorg.llm_classifier.adapters.llm.factory import get_llm
from fileorg.llm_classifier.adapters.config.file_config_adapter import get_config

# Convenience function for backward compatibility
def get_classifier(
    use_advanced_prompt: bool = False,
    prompt_version: str = "v1",
    use_few_shot: bool = False,
    use_domain_detection: bool = False,
    config: dict = None
):
    """
    Get a classifier instance (backward compatibility function).

    Args:
        use_advanced_prompt: Enable advanced prompt engineering
        prompt_version: Prompt template version ('v1' or 'v2')
        use_few_shot: Enable few-shot learning
        use_domain_detection: Enable domain detection
        config: Optional configuration dictionary

    Returns:
        CreateFolderNamer instance with legacy interface
    """
    return CreateFolderNamer(
        use_advanced_prompt=use_advanced_prompt,
        prompt_version=prompt_version,
        use_few_shot=use_few_shot,
        use_domain_detection=use_domain_detection,
        config=config
    )


__all__ = [
    # New Architecture
    "create_classifier_system",
    "run_classification",
    "DocumentClassificationService",
    "FolderRemappingService",
    "FileProcessingService",
    "CreateFolderNamer",
    # Legacy Compatibility
    "get_llm",
    "get_config",
    "get_classifier",
]

__version__ = "3.0.0"  # Major version bump for architectural change
