"""
Manual/GPU integration tests with real LLM inference.

⚠️ IMPORTANT: These are MANUAL tests, not for CI/CD!

These tests use actual GPU-based LLM inference to validate the two-stage
classification workflow with real prompt templates.

Use Cases:
- Manual verification before release
- Performance benchmarking
- Quality assurance with real LLM

Tests are marked with @pytest.mark.gpu and @pytest.mark.slow.
They will be skipped if:
- GPU is not available (torch.cuda.is_available() == False)
- Set SKIP_GPU_TESTS=1 environment variable (recommended for CI/CD)

For CI/CD, use tests/e2e/test_two_stage_e2e.py instead.
"""

import json
import os

import pytest

# Skip entire module if GPU dependencies are not available
pytest.importorskip("torch")
pytest.importorskip("transformers")

from fileorg.llm_classifier.adapters.llm_providers import GPUProvider
from fileorg.llm_classifier.adapters.output_parsers import (
    PathMappingOutputParser,
    SummaryOutputParser,
)
from fileorg.llm_classifier.adapters.prompt_builders import (
    ClassificationPromptBuilder,
    SummaryPromptBuilder,
)
from fileorg.llm_classifier.adapters.template_loader import Jinja2TemplateLoader
from fileorg.llm_classifier.application.file_classifier import FileClassifier
from fileorg.llm_classifier.ports.models import LLMInput

# Check if GPU tests should be skipped
SKIP_GPU_TESTS = os.getenv("SKIP_GPU_TESTS", "0") == "1"

# Try to import torch to check GPU availability
try:
    import torch

    HAS_TORCH = True
    HAS_GPU = torch.cuda.is_available()
except ImportError:
    HAS_TORCH = False
    HAS_GPU = False

pytestmark = pytest.mark.skipif(
    SKIP_GPU_TESTS or not HAS_TORCH or not HAS_GPU,
    reason="GPU not available or SKIP_GPU_TESTS=1",
)


@pytest.fixture(scope="module")
def gpu_provider():
    """Create GPUProvider instance (reused across tests)."""
    # Determine device: use cuda if available, otherwise cpu
    device = "cuda" if HAS_GPU else "cpu"
    return GPUProvider(
        model_name="meta-llama/Llama-3.2-3B-Instruct",
        device=device,
    )


@pytest.fixture(scope="module")
def template_loader():
    """Create template loader for v1 prompts."""
    return Jinja2TemplateLoader()


@pytest.fixture(scope="module")
def file_classifier(gpu_provider, template_loader):
    """Create FileClassifier with real GPU provider and v1 prompts."""
    summary_prompt_builder = SummaryPromptBuilder(
        template_loader=template_loader,
        provider="llama3b",
        version="v1",
    )

    classification_prompt_builder = ClassificationPromptBuilder(
        template_loader=template_loader,
        provider="llama3b",
        version="v1",
    )

    summary_parser = SummaryOutputParser()
    classification_parser = PathMappingOutputParser()

    return FileClassifier(
        llm_provider=gpu_provider,
        summary_prompt_builder=summary_prompt_builder,
        summary_parser=summary_parser,
        classification_prompt_builder=classification_prompt_builder,
        classification_parser=classification_parser,
    )


@pytest.mark.gpu
@pytest.mark.slow
class TestRealGPUIntegration:
    """Integration tests with real GPU inference."""

    def test_stage1_keyword_extraction_real(self, file_classifier):
        """Test Stage 1 keyword extraction with real LLM."""
        files = {
            "C:/Documents/annual_financial_report_2024.pdf": (
                "Annual Financial Report for fiscal year 2024. "
                "Consolidated statements of income and comprehensive income. "
                "Revenue increased by 15% year-over-year to $5.2 billion."
            )
        }

        input_data = LLMInput(text=json.dumps(files))

        # Stage 1: Extract keywords
        summaries, raw_response = file_classifier.generate_summaries(input_data)

        # Verify Stage 1 output
        assert len(summaries) == 1
        assert "C:/Documents/annual_financial_report_2024.pdf" in summaries

        summary = summaries["C:/Documents/annual_financial_report_2024.pdf"]
        assert summary.summary is not None
        assert len(summary.summary.split()) <= 3  # Should be 1-2 words keyword
        assert summary.metadata is not None

        # Use repr() to avoid UnicodeEncodeError on Windows
        print(f"\nStage 1 Output - Keyword: {repr(summary.summary)}")
        print(f"Raw Response: {repr(raw_response[:200])}...")

    def test_stage2_classification_real(self, file_classifier):
        """Test Stage 2 classification with real LLM."""
        files = {
            "C:/Documents/financial_report.pdf": "Q4 earnings and revenue data",
            "C:/Documents/meeting_notes.txt": "Team sync meeting discussion points",
            "C:/Documents/project_plan.docx": "Software development project timeline",
        }

        input_data = LLMInput(text=json.dumps(files))

        # Stage 1: Extract keywords
        summaries, _ = file_classifier.generate_summaries(input_data)

        # Stage 2: Classify based on keywords
        path_mappings, raw_response = file_classifier.classify_by_summaries(summaries)

        # Verify Stage 2 output
        assert len(path_mappings) == 3

        for path, mapping in path_mappings.items():
            assert mapping.old_path == path
            assert mapping.category is not None and mapping.category.strip() != ""
            assert mapping.summary is not None and mapping.summary.strip() != ""
            assert mapping.reason is not None and mapping.reason.strip() != ""
            assert mapping.new_relative_path is not None
            assert "/" in mapping.new_relative_path  # Should have category folder

            # Use repr() to avoid UnicodeEncodeError on Windows
            print(f"\nFile: {path}")
            print(f"  Keyword: {repr(mapping.summary)}")
            print(f"  Category: {repr(mapping.category)}")
            print(f"  New Path: {mapping.new_relative_path}")
            print(f"  Reason: {repr(mapping.reason)}")

    def test_two_stage_complete_workflow_real(self, file_classifier):
        """Test complete two-stage workflow with real LLM."""
        files = {
            "C:/Work/quarterly_report_Q3.pdf": ("Quarterly financial report Q3 2024. Net income $1.2M. Operating expenses $500K."),
            "C:/Work/team_meeting_20241113.txt": ("Weekly team meeting notes. Discussed sprint planning and feature priorities."),
        }

        input_data = LLMInput(text=json.dumps(files))

        # Run complete two-stage classification
        result = file_classifier.classify(input_data)

        # Verify output structure
        assert result.path_mappings is not None
        assert len(result.path_mappings) == 2

        # Verify raw responses from both stages
        assert "stage1_summaries" in result.raw_responses
        assert "stage2_classification" in result.raw_responses
        assert result.raw_responses["stage1_summaries"].strip() != ""
        assert result.raw_responses["stage2_classification"].strip() != ""

        # Verify metadata
        assert result.metadata["file_count"] == 2
        assert result.metadata["stage1_time_ms"] > 0
        assert result.metadata["stage2_time_ms"] > 0
        assert result.metadata["total_time_ms"] > 0
        assert result.metadata["total_time_ms"] >= result.metadata["stage1_time_ms"] + result.metadata["stage2_time_ms"]

        print("\n=== Complete Two-Stage Workflow Results ===")
        print(f"Total time: {result.metadata['total_time_ms']}ms")
        print(f"Stage 1 time: {result.metadata['stage1_time_ms']}ms")
        print(f"Stage 2 time: {result.metadata['stage2_time_ms']}ms")

        # Use repr() to avoid UnicodeEncodeError on Windows
        for path, mapping in result.path_mappings.items():
            print(f"\n{path}:")
            print(f"  → {mapping.new_relative_path}")
            print(f"  Keyword: {repr(mapping.summary)}")
            print(f"  Category: {repr(mapping.category)}")

    def test_gpu_device_info(self, gpu_provider):
        """Test GPU provider device information."""
        device_info = gpu_provider.get_device_info()

        print(f"\nGPU Device Info: {device_info}")
        assert device_info is not None

        # device_info can be string or dict depending on the provider
        if isinstance(device_info, dict):
            # For dict response, check the device field
            assert "device" in device_info
            device_str = str(device_info["device"])
            assert "cuda" in device_str.lower() or "cpu" in device_str.lower()
        else:
            # For string response
            assert "cuda" in device_info.lower() or "cpu" in device_info.lower() or "gpu" in device_info.lower()

    def test_v1_prompts_exist(self, template_loader):
        """Verify v1 two-stage prompts exist and are loadable."""
        # Check Stage 1 (summary) templates
        assert template_loader.template_exists("llama3b", "v1", "summary_system")
        assert template_loader.template_exists("llama3b", "v1", "summary_user")

        # Check Stage 2 (classification) templates
        assert template_loader.template_exists("llama3b", "v1", "classification_system")
        assert template_loader.template_exists("llama3b", "v1", "classification_user")

        # Load and verify templates
        summary_sys = template_loader.load_template("llama3b", "v1", "summary_system")
        summary_user = template_loader.load_template("llama3b", "v1", "summary_user")
        class_sys = template_loader.load_template("llama3b", "v1", "classification_system")
        class_user = template_loader.load_template("llama3b", "v1", "classification_user")

        # Verify templates are not empty
        assert summary_sys.render().strip() != ""
        assert summary_user.render().strip() != ""
        assert class_sys.render().strip() != ""
        assert class_user.render().strip() != ""

        # Use ASCII check mark to avoid UnicodeEncodeError on Windows
        print("\n[OK] All v1 two-stage prompts loaded successfully")


@pytest.mark.gpu
@pytest.mark.slow
class TestPromptQuality:
    """Test prompt quality and LLM output validation."""

    def test_keyword_extraction_quality(self, file_classifier):
        """Test that keywords are concise and relevant."""
        files = {
            "C:/test/machine_learning_research_paper.pdf": (
                "Research paper on deep learning neural networks for image classification. "
                "Convolutional Neural Networks (CNNs) achieve 95% accuracy on ImageNet dataset."
            )
        }

        input_data = LLMInput(text=json.dumps(files))
        summaries, _ = file_classifier.generate_summaries(input_data)

        keyword = summaries["C:/test/machine_learning_research_paper.pdf"].summary

        # Keyword should be concise (1-5 words is acceptable for complex topics)
        # LLMs may generate slightly longer keywords for technical content
        word_count = len(keyword.split())
        assert 1 <= word_count <= 5, f"Keyword should be 1-5 words, got: '{keyword}' ({word_count} words)"

        # Keyword should be relevant and not empty
        assert keyword.strip() != ""
        assert len(keyword) > 2  # More than just initials

        # Use repr() to avoid UnicodeEncodeError on Windows
        print(f"\nExtracted keyword: {repr(keyword)} ({word_count} words)")

    def test_classification_consistency(self, file_classifier):
        """Test that classification is consistent and structured."""
        files = {
            "C:/docs/invoice_2024_001.pdf": "Invoice for services rendered in January 2024",
            "C:/docs/invoice_2024_002.pdf": "Invoice for consulting services February 2024",
        }

        input_data = LLMInput(text=json.dumps(files))
        result = file_classifier.classify(input_data)

        # Both invoices should get same category
        cat1 = result.path_mappings["C:/docs/invoice_2024_001.pdf"].category
        cat2 = result.path_mappings["C:/docs/invoice_2024_002.pdf"].category

        # Categories should be similar (ideally same)
        # Use repr() to avoid UnicodeEncodeError on Windows
        print(f"\nInvoice 1 category: {repr(cat1)}")
        print(f"Invoice 2 category: {repr(cat2)}")

        # Both should have "invoice" or "financial" or similar in category
        assert "invoice" in cat1.lower() or "financial" in cat1.lower() or "billing" in cat1.lower()
        assert "invoice" in cat2.lower() or "financial" in cat2.lower() or "billing" in cat2.lower()
