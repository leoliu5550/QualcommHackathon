"""
Integration test fixtures for LLM classifier.

This module provides fixtures for end-to-end testing with real LLM models.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict

import pytest
import torch
from loguru import logger

# ============================================================================
# GPU Detection
# ============================================================================


def has_gpu() -> bool:
    """Check if GPU/CUDA is available."""
    return torch.cuda.is_available()


def has_sufficient_memory(min_gb: float = 4.0) -> bool:
    """Check if GPU has sufficient memory."""
    if not has_gpu():
        return False
    try:
        total_memory = torch.cuda.get_device_properties(0).total_memory
        total_gb = total_memory / (1024**3)
        return total_gb >= min_gb
    except Exception:
        return False


# ============================================================================
# Path Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get the project root directory."""
    # Navigate from fileorg/llm_classifier/tests/integration to project root
    return Path(__file__).parent.parent.parent.parent.parent


@pytest.fixture(scope="session")
def sample_files_dir(project_root) -> Path:
    """Get the sample files directory path (using ./tests/example_data)."""
    return project_root / "tests" / "example_data"


# ============================================================================
# Sample File Data Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def sample_file_paths(sample_files_dir) -> Dict[str, Path]:
    """Get paths to real example files from ./tests/example_data."""
    return {
        "pdf": sample_files_dir / "CH04account.pdf",
        "excel": sample_files_dir / "Excel_Function.xlsx",
        "json": sample_files_dir / "customer_order.json",
        "markdown": sample_files_dir / "customer_order.md",
        "csv": sample_files_dir / "202510D" / "aqx_p_432.csv",
    }


@pytest.fixture(scope="session")
def sample_file_contents(sample_file_paths) -> Dict[str, str]:
    """
    Read contents of all sample files.

    For binary files (PDF, Excel), returns a placeholder string.
    For text files, returns actual content.
    """
    contents = {}
    for key, path in sample_file_paths.items():
        if not path.exists():
            logger.warning(f"Sample file not found: {path}")
            contents[key] = f"[File not found: {path.name}]"
            continue

        try:
            if key in ["pdf", "excel"]:
                # Binary files - use placeholder
                contents[key] = f"[Binary file: {path.name}]"
            else:
                # Text files - read actual content
                with open(path, "r", encoding="utf-8") as f:
                    contents[key] = f.read()
        except Exception as e:
            logger.error(f"Failed to read {path}: {e}")
            contents[key] = f"[Error reading file: {path.name}]"

    return contents


@pytest.fixture(scope="session")
def sample_files_json(sample_file_paths, sample_file_contents) -> str:
    """
    Create JSON-formatted file data for LLM input.

    Format: {"file_path": "file_content", ...}
    """
    file_data = {}
    for key, path in sample_file_paths.items():
        # Use relative path from sample_files dir
        rel_path = path.name
        file_data[rel_path] = sample_file_contents[key]

    return json.dumps(file_data, ensure_ascii=False, indent=2)


# ============================================================================
# LLM Provider Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def llm_model_name() -> str:
    """
    Get LLM model name from environment or use default.

    Override with: export LLM_MODEL_NAME="meta-llama/Llama-3.2-3B-Instruct"
    """
    return os.getenv("LLM_MODEL_NAME", "meta-llama/Llama-3.2-3B-Instruct")


@pytest.fixture(scope="session")
def huggingface_provider(llm_model_name):
    """
    Create GPU provider (lazy loading, session-scoped).

    This fixture is only created once per test session to avoid
    reloading the model multiple times.
    """
    from fileorg.llm_classifier.adapters import GPUProvider

    provider = GPUProvider(
        model_name=llm_model_name,
        device=None,  # Auto-detect
        torch_dtype=None,  # Auto-detect
    )

    # Log device info
    device_info = provider.get_device_info()
    print(f"\n{'=' * 60}")
    print("LLM Provider Device Info:")
    print(f"  Model: {llm_model_name}")
    print(f"  Device: {device_info['device']}")
    print(f"  Dtype: {device_info['dtype']}")
    print(f"  CUDA Available: {device_info['cuda_available']}")
    if device_info["cuda_available"]:
        print(f"  CUDA Device: {device_info.get('cuda_device_name', 'N/A')}")
        mem_gb = device_info.get("cuda_memory_allocated", 0) / (1024**3)
        print(f"  Memory Allocated: {mem_gb:.2f} GB")
    print(f"{'=' * 60}\n")

    return provider


@pytest.fixture(scope="session")
def llama_prompt_builder():
    """Create Llama 3B prompt builder."""
    from fileorg.llm_classifier.adapters.template_loader import Jinja2TemplateLoader
    from fileorg.llm_classifier.application.llama_prompt_builder import LlamaPromptBuilder

    template_loader = Jinja2TemplateLoader()
    return LlamaPromptBuilder(template_loader=template_loader, provider="llama3b", version="v1")


@pytest.fixture(scope="session")
def json_output_parser():
    """Create JSON output parser."""
    from fileorg.llm_classifier.application.json_output_parser import JSONOutputParser

    return JSONOutputParser()


@pytest.fixture(scope="session")
def file_classifier(huggingface_provider, llama_prompt_builder, json_output_parser):
    """Create file classifier with HuggingFace backend and JSON parser."""
    from fileorg.llm_classifier.application.file_classifier import FileClassifier

    return FileClassifier(
        llm_provider=huggingface_provider,
        prompt_builder=llama_prompt_builder,
        output_parser=json_output_parser,
    )


# ============================================================================
# Suggested Categories Fixtures
# ============================================================================


@pytest.fixture
def suggested_categories_basic() -> list:
    """Basic suggested categories for testing."""
    return ["Code", "Documentation", "Data", "Configuration"]


@pytest.fixture
def suggested_categories_detailed() -> list:
    """Detailed suggested categories."""
    return ["Source Code", "Documentation", "Data Files", "Configuration Files", "Meeting Notes", "Reports"]


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers and logging."""
    config.addinivalue_line("markers", "gpu: tests that require GPU/CUDA (deselect with '-m \"not gpu\"')")
    config.addinivalue_line("markers", "integration: integration tests that may be slow")

    # Enable detailed logging for integration tests
    # Remove default logger and add custom one for tests
    logger.remove()  # Remove default handler

    # Add console handler with detailed format
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        level="DEBUG",  # Show all logs including DEBUG
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info("=" * 70)
    logger.info("Integration Test Session Started - Logging Enabled")
    logger.info("=" * 70)


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """
    Setup logging for integration tests (auto-used for all tests).

    This fixture ensures that:
    1. All log messages are displayed during test execution
    2. Log level is set to DEBUG for maximum visibility
    3. GPU-related operations are logged
    """
    logger.info("Setting up integration test logging...")
    logger.debug("Debug logging is enabled")
    yield
    logger.info("Integration test session completed")


@pytest.fixture(scope="session", autouse=True)
def enable_gpu_logging():
    """Enable detailed logging for GPU operations."""
    # Set environment variable to enable development mode logging
    os.environ["FILEORG_ENV"] = "development"
    logger.info("GPU logging enabled for integration tests")
    yield
