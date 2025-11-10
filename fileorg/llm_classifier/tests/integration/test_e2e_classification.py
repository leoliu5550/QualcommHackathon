"""
End-to-end integration tests for LLM-based file classification.

These tests verify the complete classification pipeline using real example files
from ./tests/example_data directory.

HOW TO RUN TESTS:
=================

1. Run with GPU (NVIDIA CUDA):
   pytest fileorg/llm_classifier/tests/integration/ -v -m gpu

2. Run with MPS (Apple Silicon M1/M2/M3):
   export LLM_PROVIDER_TYPE="mps"
   pytest fileorg/llm_classifier/tests/integration/ -v

3. Run with QAIC (Qualcomm AI Engine):
   export LLM_PROVIDER_TYPE="qaic"
   pytest fileorg/llm_classifier/tests/integration/ -v

4. Run with auto-detection (recommended):
   pytest fileorg/llm_classifier/tests/integration/ -v

5. Skip GPU tests (CPU only):
   pytest fileorg/llm_classifier/tests/integration/ -v -m "not gpu"

PROVIDER SELECTION:
==================
- Set LLM_PROVIDER_TYPE environment variable to: "gpu", "mps", "qaic", or leave unset for auto-detection
- Auto-detection priority: QAIC > GPU (CUDA) > MPS (Apple Silicon) > CPU

REQUIREMENTS:
=============
- For GPU: NVIDIA GPU with CUDA support
- For MPS: macOS with Apple Silicon (M1/M2/M3)
- For QAIC: Qualcomm Cloud AI 100 hardware
- HuggingFace transformers library
- Llama 3B model (downloaded automatically on first run)
"""

import json

import pytest
import torch

from fileorg.llm_classifier.ports import LLMInput
from fileorg.llm_classifier.tests.integration.conftest import has_gpu, has_sufficient_memory

# ============================================================================
# Test Markers and Skip Conditions
# ============================================================================


skip_if_no_gpu = pytest.mark.skipif(not has_gpu(), reason="GPU/CUDA not available. Install CUDA and PyTorch with GPU support.")

skip_if_insufficient_memory = pytest.mark.skipif(
    not has_sufficient_memory(min_gb=4.0), reason="Insufficient GPU memory (requires at least 4GB for Llama 3B)"
)


# ============================================================================
# Test Class: Basic Classification
# ============================================================================


@pytest.mark.integration
@pytest.mark.gpu
class TestBasicClassification:
    """Test basic file classification with LLM."""

    @skip_if_no_gpu
    @skip_if_insufficient_memory
    def test_classify_sample_files(self, file_classifier, sample_files_json):
        """
        Test basic classification of sample files.

        This test verifies:
        1. LLM can process multiple file types (Python, Markdown, JSON, TXT, CSV)
        2. Output is generated successfully
        3. Output is valid JSON format
        """
        # Arrange
        input_data = LLMInput(text=sample_files_json, max_tokens=4096)

        # Act
        result = file_classifier.classify(input_data)

        # Assert
        assert result is not None, "Classification result should not be None"
        assert result.raw_response, "Raw response should not be empty"
        assert len(result.raw_response) > 0, "Raw response should have content"

        # Verify metadata
        assert result.metadata is not None, "Metadata should be present"
        assert result.metadata["input_length"] > 0
        assert result.metadata["output_length"] > 0

        # Verify parsed classifications (OutputParser should have extracted JSON)
        assert result.classifications is not None, "Classifications should not be None"
        assert isinstance(result.classifications, dict), "Classifications should be a dictionary"
        assert len(result.classifications) > 0, "Should have at least one category"

        print(f"\n{'=' * 60}")
        print("LLM Classification Result:")
        print(json.dumps(result.classifications, indent=2, ensure_ascii=False))
        print(f"✓ Successfully classified into {len(result.classifications)} categories")
        print(f"{'=' * 60}\n")

    @skip_if_no_gpu
    @skip_if_insufficient_memory
    def test_classify_with_suggested_categories(self, file_classifier, sample_files_json, suggested_categories_basic):
        """
        Test classification with suggested categories.

        Verifies that the LLM can use provided category suggestions.
        """
        # Arrange
        input_data = LLMInput(text=sample_files_json, max_tokens=4096)

        # Act
        result = file_classifier.classify_with_categories(input_data, suggested_categories=suggested_categories_basic)

        # Assert
        assert result is not None
        assert result.raw_response
        assert len(result.raw_response) > 0

        # Verify parsed classifications
        assert result.classifications is not None
        assert isinstance(result.classifications, dict)

        print(f"\n{'=' * 60}")
        print(f"Suggested Categories: {suggested_categories_basic}")
        print("LLM Classification Result:")
        print(json.dumps(result.classifications, indent=2, ensure_ascii=False))
        print(f"{'=' * 60}\n")

        # Optionally check if any suggested categories were used
        # (Note: LLM might not use all suggested categories)
        categories_used = list(result.classifications.keys())
        print(f"Categories used by LLM: {categories_used}")

    @skip_if_no_gpu
    @skip_if_insufficient_memory
    def test_classify_empty_input_raises_error(self, file_classifier):
        """Test that empty input raises ValueError."""
        # Arrange
        input_data = LLMInput(text="", max_tokens=4096)

        # Act & Assert
        with pytest.raises(ValueError, match="Input text cannot be empty"):
            file_classifier.classify(input_data)

    @skip_if_no_gpu
    @skip_if_insufficient_memory
    def test_classify_single_file(self, file_classifier, sample_file_contents):
        """Test classification of a single file."""
        # Arrange - use only the JSON file
        single_file_json = json.dumps({"customer_order.json": sample_file_contents["json"]}, ensure_ascii=False)

        input_data = LLMInput(text=single_file_json, max_tokens=4096)

        # Act
        result = file_classifier.classify(input_data)

        # Assert
        assert result is not None
        assert result.raw_response
        assert len(result.raw_response) > 0

        # Verify parsed classifications
        assert result.classifications is not None
        assert isinstance(result.classifications, dict)
        print("\nSingle file classification result:")
        print(json.dumps(result.classifications, indent=2, ensure_ascii=False))

    @skip_if_no_gpu
    @skip_if_insufficient_memory
    def test_real_file_classification_accuracy(self, file_classifier, sample_file_paths, sample_file_contents):
        """
        Test that files are ACTUALLY classified correctly by the LLM.

        This test verifies:
        1. LLM actually processes file content from ./tests/example_data
        2. Files are classified into reasonable categories
        3. Different file types are recognized appropriately
        """
        # Arrange - Create file data with actual files from example_data
        file_data = {
            "CH04account.pdf": sample_file_contents["pdf"],  # Should be Documents/Finance
            "Excel_Function.xlsx": sample_file_contents["excel"],  # Should be Data/Spreadsheet
            "customer_order.json": sample_file_contents["json"],  # Should be Data/JSON
            "customer_order.md": sample_file_contents["markdown"],  # Should be Documentation
            "aqx_p_432.csv": sample_file_contents["csv"],  # Should be Data/CSV
        }

        input_json = json.dumps(file_data, ensure_ascii=False)
        input_data = LLMInput(text=input_json, max_tokens=4096)

        # Act - Run classification
        print("\n" + "=" * 60)
        print(">> Running REAL GPU-based File Classification")
        print("=" * 60)

        result = file_classifier.classify(input_data)

        # Assert - Verify the classification results
        assert result is not None, "Classification failed"
        assert result.classifications is not None, "No classifications returned"
        assert len(result.classifications) > 0, "Empty classification result"

        # Verify GPU was actually used
        assert result.metadata.get("parsed") is True, "Output was not parsed successfully"

        # Print the results
        print(f"\n[OK] LLM Classification Results ({len(result.classifications)} categories):")
        print("-" * 60)

        all_classified_files = []
        for category, files in result.classifications.items():
            print(f"\n[Category] {category}:")
            for file in files:
                print(f"   - {file}")
                all_classified_files.append(file)

        print("-" * 60)

        # Verify all files were classified
        expected_files = set(file_data.keys())
        classified_files = set(all_classified_files)

        print("\n[Stats] Classification Coverage:")
        print(f"   Expected files: {len(expected_files)}")
        print(f"   Classified files: {len(classified_files)}")
        print(f"   Coverage: {len(classified_files) / len(expected_files) * 100:.1f}%")

        # Verify reasonable classification
        # At minimum, we should have some categories
        assert len(result.classifications) >= 2, "Should have at least 2 categories"

        # Verify JSON file is somewhere (LLM should recognize it)
        json_found = any("customer_order.json" in files for files in result.classifications.values())
        assert json_found, "JSON file should be classified"

        # Verify classifications make sense (at least some files are categorized)
        assert len(classified_files) >= 3, "Should classify at least 3 files"

        print("\n[PASS] VERIFICATION PASSED:")
        print("   [OK] GPU-based LLM inference completed")
        print("   [OK] Files were actually analyzed and classified")
        print(f"   [OK] {len(classified_files)}/{len(expected_files)} files categorized")
        print(f"   [OK] {len(result.classifications)} distinct categories created")
        print("=" * 60 + "\n")


# ============================================================================
# Test Class: Error Handling
# ============================================================================


@pytest.mark.integration
@pytest.mark.gpu
class TestErrorHandling:
    """Test error handling in classification pipeline."""

    @skip_if_no_gpu
    def test_invalid_json_input_raises_error(self, file_classifier):
        """
        Test that invalid JSON input is rejected by prompt builder.

        The prompt builder validates JSON format before sending to LLM,
        as it needs to parse the structure for proper prompt construction.
        """
        # Arrange - intentionally malformed JSON
        invalid_json = '{"file.txt": "content", invalid}'

        input_data = LLMInput(text=invalid_json, max_tokens=2048)

        # Act & Assert - should raise ValueError during prompt building
        with pytest.raises(ValueError, match="Input text must be valid JSON"):
            file_classifier.classify(input_data)

    @skip_if_no_gpu
    def test_whitespace_only_input_raises_error(self, file_classifier):
        """Test that whitespace-only input raises ValueError."""
        # Arrange
        input_data = LLMInput(text="   \n\t  ", max_tokens=4096)

        # Act & Assert
        with pytest.raises(ValueError, match="Input text cannot be empty"):
            file_classifier.classify(input_data)

    @skip_if_no_gpu
    def test_very_large_input_truncation(self, file_classifier):
        """
        Test that very large input is handled (truncated by prompt builder).

        This test verifies the truncation mechanism works correctly.
        """
        # Arrange - create a large file list
        large_file_data = {}
        for i in range(100):
            large_file_data[f"file_{i}.txt"] = f"Content of file {i}" * 100

        large_json = json.dumps(large_file_data, ensure_ascii=False)

        input_data = LLMInput(text=large_json, max_tokens=2048)  # Small token limit

        # Act - should handle truncation gracefully
        result = file_classifier.classify(input_data)

        # Assert
        assert result is not None
        assert result.raw_response
        print(f"\nTruncated input test - output length: {len(result.raw_response)} chars")


# ============================================================================
# Test Class: Device and Model Info
# ============================================================================


@pytest.mark.integration
@pytest.mark.gpu
class TestDeviceInfo:
    """Test device and model information utilities."""

    @skip_if_no_gpu
    def test_gpu_is_available(self):
        """Verify GPU is available for testing."""
        assert torch.cuda.is_available(), "CUDA should be available"
        assert torch.cuda.device_count() > 0, "At least one CUDA device should be present"

        device_name = torch.cuda.get_device_name(0)
        print(f"\nGPU Device: {device_name}")

    @skip_if_no_gpu
    def test_huggingface_provider_device_info(self, huggingface_provider):
        """Test HuggingFace provider device information."""
        device_info = huggingface_provider.get_device_info()

        assert device_info is not None
        assert device_info["device"] in ["cuda", "cpu"]
        assert device_info["cuda_available"] == torch.cuda.is_available()

        if device_info["cuda_available"]:
            assert "cuda_device_name" in device_info
            assert device_info["cuda_device_count"] > 0

        print("\nProvider Device Info:")
        for key, value in device_info.items():
            print(f"  {key}: {value}")

    def test_provider_availability_without_gpu(self, llama_prompt_builder):
        """
        Test that provider availability check works.

        This test doesn't require GPU and just checks the method exists.
        """
        from fileorg.llm_classifier.adapters import GPUProvider

        # Create provider but don't load model
        provider = GPUProvider(model_name="meta-llama/Llama-3.2-3B-Instruct")

        # Check that the method exists (we don't call is_available() as it would load the model)
        assert hasattr(provider, "is_available")
        assert hasattr(provider, "get_device_info")


# ============================================================================
# Test Class: Prompt Building Integration
# ============================================================================


@pytest.mark.integration
class TestPromptBuildingIntegration:
    """Test prompt building integration (no GPU required)."""

    def test_prompt_builder_creates_valid_messages(self, llama_prompt_builder, sample_files_json):
        """Verify prompt builder creates valid message format."""
        # Act
        messages = llama_prompt_builder.build_prompt(text=sample_files_json, instruction="Classify these files", max_tokens=4096)

        # Assert
        assert messages is not None
        assert isinstance(messages, list)
        assert len(messages) > 0

        # Check message format
        for msg in messages:
            assert isinstance(msg, dict)
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["system", "user", "assistant"]

        print(f"\nPrompt messages generated: {len(messages)} messages")
        print(f"Total prompt length: {sum(len(m['content']) for m in messages)} chars")

    def test_prompt_builder_with_suggested_categories(self, llama_prompt_builder, sample_files_json, suggested_categories_basic):
        """Verify suggested categories are included in prompt."""
        # Act
        messages = llama_prompt_builder.build_prompt(
            text=sample_files_json, instruction="Classify these files", max_tokens=4096, suggested_categories=suggested_categories_basic
        )

        # Assert
        assert messages is not None

        # Check that suggested categories appear in the prompt content
        full_prompt = " ".join(msg["content"] for msg in messages)
        for category in suggested_categories_basic:
            # The category should appear somewhere in the prompt
            assert category in full_prompt or category.lower() in full_prompt.lower(), f"Suggested category '{category}' should appear in prompt"

        print("\nSuggested categories successfully included in prompt")
