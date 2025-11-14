"""
Integration tests for two-stage file classification.

Tests the complete flow: Stage 1 (keyword extraction) -> Stage 2 (classification)
"""

import json

import pytest

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


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self):
        self.call_count = 0
        self.responses = [
            # Stage 1: File 1 keyword
            '{"C:/test1.pdf": "財務報告"}',
            # Stage 1: File 2 keyword
            '{"C:/test2.txt": "會議紀錄"}',
            # Stage 1: File 3 keyword
            '{"C:/test3.docx": "專案計劃"}',
            # Stage 2: All files classification
            json.dumps(
                {
                    "C:/test1.pdf": {
                        "category": "Financial Reports",
                        "summary": "財務報告",
                        "reason": "Based on keyword, this is a financial document",
                    },
                    "C:/test2.txt": {"category": "Meeting Notes", "summary": "會議紀錄", "reason": "Based on keyword, this is meeting documentation"},
                    "C:/test3.docx": {
                        "category": "Project Plans",
                        "summary": "專案計劃",
                        "reason": "Based on keyword, this is a project planning document",
                    },
                }
            ),
        ]
        self.response_index = 0

    def generate(self, messages, max_tokens=32768):
        """Generate mock responses in sequence."""
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            self.call_count += 1
            return response
        else:
            # Fallback for additional calls
            self.call_count += 1
            return '{"error": "No more mock responses"}'

    def get_device_info(self):
        return "MockProvider"


@pytest.fixture
def template_loader():
    """Create template loader."""
    return Jinja2TemplateLoader()


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def classifier(template_loader, mock_llm_provider):
    """Create FileClassifier with all dependencies."""
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
    output_parser = PathMappingOutputParser()

    return FileClassifier(
        llm_provider=mock_llm_provider,
        summary_prompt_builder=summary_prompt_builder,
        summary_parser=summary_parser,
        classification_prompt_builder=classification_prompt_builder,
        classification_parser=output_parser,
    )


@pytest.fixture
def sample_input():
    """Create sample input data."""
    files = {
        "C:/test1.pdf": "This is a financial report with Q4 earnings data.",
        "C:/test2.txt": "Meeting notes from the weekly team sync.",
        "C:/test3.docx": "Project plan for the new feature implementation.",
    }
    return LLMInput(text=json.dumps(files))


class TestTwoStageClassification:
    """Test two-stage classification integration."""

    def test_two_stage_flow(self, classifier, sample_input, mock_llm_provider):
        """Test complete two-stage classification flow."""
        result = classifier.classify(sample_input)

        # Verify LLM was called for each stage
        # Stage 1: 3 files = 3 calls
        # Stage 2: 1 call for all files
        assert mock_llm_provider.call_count == 4

        # Verify output structure
        assert result.path_mappings is not None
        assert len(result.path_mappings) == 3

        # Verify raw responses from both stages
        assert "stage1_summaries" in result.raw_responses
        assert "stage2_classification" in result.raw_responses
        assert result.raw_responses["stage1_summaries"] != ""
        assert result.raw_responses["stage2_classification"] != ""

        # Verify metadata
        assert result.metadata["file_count"] == 3
        assert "stage1_time_ms" in result.metadata
        assert "stage2_time_ms" in result.metadata
        assert "total_time_ms" in result.metadata

    def test_stage1_keyword_extraction(self, classifier, sample_input):
        """Test Stage 1 keyword extraction."""
        summaries, raw_response = classifier.generate_summaries(sample_input)

        # Verify all files have summaries
        assert len(summaries) == 3
        assert "C:/test1.pdf" in summaries
        assert "C:/test2.txt" in summaries
        assert "C:/test3.docx" in summaries

        # Verify keywords were extracted
        assert summaries["C:/test1.pdf"].summary == "財務報告"
        assert summaries["C:/test2.txt"].summary == "會議紀錄"
        assert summaries["C:/test3.docx"].summary == "專案計劃"

        # Verify raw response is combined
        assert raw_response != ""
        assert "---" in raw_response  # Separator between files

    def test_stage2_classification(self, classifier, sample_input):
        """Test Stage 2 classification."""
        # First get summaries
        summaries, _ = classifier.generate_summaries(sample_input)

        # Then classify
        path_mappings, raw_response = classifier.classify_by_summaries(summaries)

        # Verify all files are classified
        assert len(path_mappings) == 3

        # Verify mapping structure
        for path, mapping in path_mappings.items():
            assert mapping.old_path == path
            assert mapping.category != ""
            assert mapping.summary != ""
            assert mapping.reason != ""
            assert mapping.new_relative_path != ""
            assert "/" in mapping.new_relative_path  # Contains category folder

        # Verify raw response
        assert raw_response != ""

    def test_path_mapping_correctness(self, classifier, sample_input):
        """Test that path mappings are correctly assembled."""
        result = classifier.classify(sample_input)

        # Verify Financial Reports mapping
        financial_mapping = result.path_mappings["C:/test1.pdf"]
        assert financial_mapping.old_path == "C:/test1.pdf"
        assert financial_mapping.category == "Financial Reports"
        assert financial_mapping.new_relative_path == "Financial_Reports/test1.pdf"
        assert financial_mapping.summary == "財務報告"

        # Verify Meeting Notes mapping
        meeting_mapping = result.path_mappings["C:/test2.txt"]
        assert meeting_mapping.old_path == "C:/test2.txt"
        assert meeting_mapping.category == "Meeting Notes"
        assert meeting_mapping.new_relative_path == "Meeting_Notes/test2.txt"

        # Verify Project Plans mapping
        project_mapping = result.path_mappings["C:/test3.docx"]
        assert project_mapping.old_path == "C:/test3.docx"
        assert project_mapping.category == "Project Plans"
        assert project_mapping.new_relative_path == "Project_Plans/test3.docx"

    def test_empty_input_raises_error(self, classifier):
        """Test that empty input raises ValueError."""
        empty_input = LLMInput(text="")

        with pytest.raises(ValueError, match="Input text cannot be empty"):
            classifier.classify(empty_input)

    def test_invalid_json_raises_error(self, classifier):
        """Test that invalid JSON raises error."""
        invalid_input = LLMInput(text="not a json string")

        with pytest.raises(ValueError):  # Will raise in generate_summaries
            classifier.classify(invalid_input)
