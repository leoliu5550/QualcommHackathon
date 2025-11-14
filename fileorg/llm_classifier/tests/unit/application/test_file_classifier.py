"""
Unit tests for FileClassifier use case (Two-Stage Architecture).

Tests verify that FileClassifier correctly implements the IClassifierUseCase
interface and properly orchestrates the two-stage file classification workflow.
"""

import json
from unittest.mock import Mock, patch

import pytest

from fileorg.llm_classifier.application.file_classifier import FileClassifier
from fileorg.llm_classifier.ports import IClassifierUseCase
from fileorg.llm_classifier.ports.models import (
    ClassificationOutput,
    FileMapping,
    FileSummary,
    LLMInput,
)


@pytest.fixture
def mock_llm_provider():
    """Provide a mock LLM provider."""
    provider = Mock()
    provider.__class__.__name__ = "MockLLMProvider"
    # Stage 1 responses (keywords)
    provider.generate.side_effect = [
        '{"C:/test/file1.txt": "財務"}',
        '{"C:/test/file2.txt": "會議"}',
        # Stage 2 response (classification)
        json.dumps(
            {
                "C:/test/file1.txt": {"category": "Financial", "summary": "財務", "reason": "Financial document"},
                "C:/test/file2.txt": {"category": "Meetings", "summary": "會議", "reason": "Meeting notes"},
            }
        ),
    ]
    return provider


@pytest.fixture
def mock_summary_prompt_builder():
    """Provide a mock summary prompt builder (Stage 1)."""
    builder = Mock()
    builder.__class__.__name__ = "MockSummaryPromptBuilder"
    builder.build_prompt.return_value = [{"role": "system", "content": "Extract keywords"}, {"role": "user", "content": "Extract 1-2 word keywords"}]
    return builder


@pytest.fixture
def mock_classification_prompt_builder():
    """Provide a mock classification prompt builder (Stage 2)."""
    builder = Mock()
    builder.__class__.__name__ = "MockClassificationPromptBuilder"
    builder.build_prompt.return_value = [{"role": "system", "content": "Classify files"}, {"role": "user", "content": "Classify based on keywords"}]
    return builder


@pytest.fixture
def mock_summary_parser():
    """Provide a mock summary parser (Stage 1)."""
    parser = Mock()
    parser.__class__.__name__ = "MockSummaryParser"

    def parse_side_effect(text, file_path, raw_length):
        # Extract keyword from mocked LLM response
        data = json.loads(text)
        keyword = data.get(file_path, "unknown")
        return FileSummary(file_path=file_path, summary=keyword, metadata={"raw_length": raw_length})

    parser.parse.side_effect = parse_side_effect
    return parser


@pytest.fixture
def mock_classification_parser():
    """Provide a mock classification parser (Stage 2)."""
    parser = Mock()
    parser.__class__.__name__ = "MockClassificationParser"
    parser.parse.return_value = {
        "C:/test/file1.txt": FileMapping(
            old_path="C:/test/file1.txt", new_relative_path="Financial/file1.txt", category="Financial", summary="財務", reason="Financial document"
        ),
        "C:/test/file2.txt": FileMapping(
            old_path="C:/test/file2.txt", new_relative_path="Meetings/file2.txt", category="Meetings", summary="會議", reason="Meeting notes"
        ),
    }
    return parser


@pytest.fixture
def mock_validator():
    """Provide a mock text validator."""
    validator = Mock()
    validator.validate.return_value = True
    validator.validate_paths_dict.return_value = True
    return validator


@pytest.fixture
def classifier(mock_llm_provider, mock_summary_prompt_builder, mock_summary_parser, mock_classification_prompt_builder, mock_classification_parser):
    """Provide a FileClassifier with mocked dependencies."""
    return FileClassifier(
        llm_provider=mock_llm_provider,
        summary_prompt_builder=mock_summary_prompt_builder,
        summary_parser=mock_summary_parser,
        classification_prompt_builder=mock_classification_prompt_builder,
        classification_parser=mock_classification_parser,
    )


@pytest.fixture
def classifier_with_validator(
    mock_llm_provider,
    mock_summary_prompt_builder,
    mock_summary_parser,
    mock_classification_prompt_builder,
    mock_classification_parser,
    mock_validator,
):
    """Provide a FileClassifier with validator."""
    return FileClassifier(
        llm_provider=mock_llm_provider,
        summary_prompt_builder=mock_summary_prompt_builder,
        summary_parser=mock_summary_parser,
        classification_prompt_builder=mock_classification_prompt_builder,
        classification_parser=mock_classification_parser,
        validator=mock_validator,
    )


@pytest.fixture
def sample_input():
    """Provide sample LLM input."""
    files_dict = {"C:/test/file1.txt": "Sample financial content", "C:/test/file2.txt": "Sample meeting notes"}
    return LLMInput(text=json.dumps(files_dict), max_tokens=150000)


class TestFileClassifierInterface:
    """Test that FileClassifier correctly implements IClassifierUseCase interface."""

    def test_implements_interface(self, classifier):
        """Verify FileClassifier implements IClassifierUseCase."""
        assert isinstance(classifier, IClassifierUseCase)

    def test_has_classify_method(self, classifier):
        """Verify classify method exists and is callable."""
        assert hasattr(classifier, "classify")
        assert callable(classifier.classify)

    def test_has_generate_summaries_method(self, classifier):
        """Verify generate_summaries method exists and is callable."""
        assert hasattr(classifier, "generate_summaries")
        assert callable(classifier.generate_summaries)

    def test_has_classify_by_summaries_method(self, classifier):
        """Verify classify_by_summaries method exists and is callable."""
        assert hasattr(classifier, "classify_by_summaries")
        assert callable(classifier.classify_by_summaries)


class TestInitialization:
    """Test FileClassifier initialization."""

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_initialization_with_all_dependencies(
        self,
        mock_logger,
        mock_llm_provider,
        mock_summary_prompt_builder,
        mock_summary_parser,
        mock_classification_prompt_builder,
        mock_classification_parser,
        mock_validator,
    ):
        """Should initialize with all dependencies."""
        classifier = FileClassifier(
            llm_provider=mock_llm_provider,
            summary_prompt_builder=mock_summary_prompt_builder,
            summary_parser=mock_summary_parser,
            classification_prompt_builder=mock_classification_prompt_builder,
            classification_parser=mock_classification_parser,
            validator=mock_validator,
        )

        assert classifier.llm_provider is mock_llm_provider
        assert classifier.summary_prompt_builder is mock_summary_prompt_builder
        assert classifier.summary_parser is mock_summary_parser
        assert classifier.classification_prompt_builder is mock_classification_prompt_builder
        assert classifier.classification_parser is mock_classification_parser
        assert classifier.validator is mock_validator

        # Verify logger was called
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "MockLLMProvider" in log_message
        assert "enabled" in log_message

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_initialization_without_validator(
        self,
        mock_logger,
        mock_llm_provider,
        mock_summary_prompt_builder,
        mock_summary_parser,
        mock_classification_prompt_builder,
        mock_classification_parser,
    ):
        """Should initialize without validator."""
        classifier = FileClassifier(
            llm_provider=mock_llm_provider,
            summary_prompt_builder=mock_summary_prompt_builder,
            summary_parser=mock_summary_parser,
            classification_prompt_builder=mock_classification_prompt_builder,
            classification_parser=mock_classification_parser,
        )

        assert classifier.validator is None

        log_message = mock_logger.info.call_args[0][0]
        assert "disabled" in log_message


class TestValidation:
    """Test input validation."""

    def test_validate_empty_text_raises_error(self, classifier):
        """Should raise ValueError for empty text."""
        empty_input = LLMInput(text="")

        with pytest.raises(ValueError, match="Input text cannot be empty"):
            classifier._validate_input(empty_input)

    def test_validate_whitespace_only_raises_error(self, classifier):
        """Should raise ValueError for whitespace-only text."""
        whitespace_input = LLMInput(text="   \n\t  ")

        with pytest.raises(ValueError, match="Input text cannot be empty"):
            classifier._validate_input(whitespace_input)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_validate_valid_json_with_validator(self, mock_logger, classifier_with_validator, sample_input):
        """Should pass validation for valid JSON with validator."""
        # Should not raise
        classifier_with_validator._validate_input(sample_input)

        # Verify validator was called
        classifier_with_validator.validator.validate_paths_dict.assert_called_once()
        mock_logger.debug.assert_called_with("Input validation passed")

    def test_validate_without_validator_skips_validation(self, classifier, sample_input):
        """Should skip detailed validation when no validator is provided."""
        # Should not raise
        classifier._validate_input(sample_input)


class TestGenerateSummaries:
    """Test Stage 1: Keyword generation."""

    def test_generate_summaries_returns_dict_and_raw(self, classifier, sample_input):
        """Should return summaries dict and raw response."""
        summaries, raw_response = classifier.generate_summaries(sample_input)

        assert isinstance(summaries, dict)
        assert isinstance(raw_response, str)
        assert len(summaries) == 2
        assert "---" in raw_response  # Separator

    def test_generate_summaries_calls_llm_for_each_file(self, classifier, sample_input, mock_llm_provider):
        """Should call LLM once for each file."""
        summaries, _ = classifier.generate_summaries(sample_input)

        # Should be called twice (once per file)
        assert mock_llm_provider.generate.call_count >= 2

    def test_generate_summaries_uses_summary_prompt_builder(self, classifier, sample_input, mock_summary_prompt_builder):
        """Should use summary_prompt_builder for prompts."""
        summaries, _ = classifier.generate_summaries(sample_input)

        # Should be called for each file
        assert mock_summary_prompt_builder.build_prompt.call_count == 2

    def test_generate_summaries_uses_summary_parser(self, classifier, sample_input, mock_summary_parser):
        """Should use summary_parser to parse keywords."""
        summaries, _ = classifier.generate_summaries(sample_input)

        # Should be called for each file
        assert mock_summary_parser.parse.call_count == 2

    def test_generate_summaries_returns_file_summaries(self, classifier, sample_input):
        """Should return FileSummary objects."""
        summaries, _ = classifier.generate_summaries(sample_input)

        for path, summary in summaries.items():
            assert isinstance(summary, FileSummary)
            assert summary.file_path == path
            assert summary.summary is not None


class TestClassifyBySummaries:
    """Test Stage 2: Classification based on keywords."""

    def test_classify_by_summaries_returns_mappings_and_raw(self, classifier, sample_input):
        """Should return path mappings and raw response."""
        # First generate summaries
        summaries, _ = classifier.generate_summaries(sample_input)

        # Then classify
        path_mappings, raw_response = classifier.classify_by_summaries(summaries)

        assert isinstance(path_mappings, dict)
        assert isinstance(raw_response, str)
        assert len(path_mappings) == 2

    def test_classify_by_summaries_uses_classification_prompt_builder(self, classifier, sample_input, mock_classification_prompt_builder):
        """Should use classification_prompt_builder."""
        summaries, _ = classifier.generate_summaries(sample_input)
        path_mappings, _ = classifier.classify_by_summaries(summaries)

        # Should be called once with all keywords
        mock_classification_prompt_builder.build_prompt.assert_called_once()

    def test_classify_by_summaries_uses_classification_parser(self, classifier, sample_input, mock_classification_parser):
        """Should use classification_parser."""
        summaries, _ = classifier.generate_summaries(sample_input)
        path_mappings, _ = classifier.classify_by_summaries(summaries)

        # Should be called once
        mock_classification_parser.parse.assert_called_once()

    def test_classify_by_summaries_returns_file_mappings(self, classifier, sample_input):
        """Should return FileMapping objects."""
        summaries, _ = classifier.generate_summaries(sample_input)
        path_mappings, _ = classifier.classify_by_summaries(summaries)

        for path, mapping in path_mappings.items():
            assert isinstance(mapping, FileMapping)
            assert mapping.old_path == path


class TestClassifyMethod:
    """Test main classify method (two-stage orchestration)."""

    def test_classify_returns_classification_output(self, classifier, sample_input):
        """Should return ClassificationOutput."""
        result = classifier.classify(sample_input)

        assert isinstance(result, ClassificationOutput)
        assert result.path_mappings is not None
        assert result.raw_responses is not None
        assert result.metadata is not None

    def test_classify_includes_stage1_and_stage2_raw_responses(self, classifier, sample_input):
        """Should include raw responses from both stages."""
        result = classifier.classify(sample_input)

        assert "stage1_summaries" in result.raw_responses
        assert "stage2_classification" in result.raw_responses
        assert isinstance(result.raw_responses["stage1_summaries"], str)
        assert isinstance(result.raw_responses["stage2_classification"], str)

    def test_classify_includes_metadata(self, classifier, sample_input):
        """Should include metadata with timing information."""
        result = classifier.classify(sample_input)

        assert "file_count" in result.metadata
        assert "stage1_time_ms" in result.metadata
        assert "stage2_time_ms" in result.metadata
        assert "total_time_ms" in result.metadata
        assert result.metadata["file_count"] == 2

    def test_classify_calls_generate_summaries(self, classifier, sample_input):
        """Should call generate_summaries internally."""
        with patch.object(classifier, "generate_summaries", wraps=classifier.generate_summaries) as mock_method:
            classifier.classify(sample_input)
            mock_method.assert_called_once()

    def test_classify_calls_classify_by_summaries(self, classifier, sample_input):
        """Should call classify_by_summaries internally."""
        with patch.object(classifier, "classify_by_summaries", wraps=classifier.classify_by_summaries) as mock_method:
            classifier.classify(sample_input)
            mock_method.assert_called_once()

    def test_classify_validates_input_first(self, classifier_with_validator):
        """Should validate input before processing."""
        empty_input = LLMInput(text="")

        with pytest.raises(ValueError, match="Input text cannot be empty"):
            classifier_with_validator.classify(empty_input)


class TestErrorHandling:
    """Test error handling."""

    def test_generate_summaries_handles_llm_error(self, classifier, sample_input, mock_llm_provider):
        """Should handle LLM generation errors in Stage 1."""
        mock_llm_provider.generate.side_effect = Exception("LLM error")

        with pytest.raises(RuntimeError, match="Keyword extraction failed"):
            classifier.generate_summaries(sample_input)

    def test_classify_by_summaries_handles_llm_error(self, classifier, sample_input):
        """Should handle LLM generation errors in Stage 2."""
        summaries = {"C:/test/file1.txt": FileSummary(file_path="C:/test/file1.txt", summary="財務", metadata={})}

        # Reset side_effect and set new error
        classifier.llm_provider.generate.side_effect = Exception("LLM error")

        with pytest.raises(RuntimeError, match="Classification failed"):
            classifier.classify_by_summaries(summaries)

    def test_classify_propagates_validation_error(self, classifier_with_validator):
        """Should propagate validation errors."""
        classifier_with_validator.validator.validate_paths_dict.return_value = False

        files_dict = {"invalid_path": "content"}
        invalid_input = LLMInput(text=json.dumps(files_dict))

        with pytest.raises(ValueError):
            classifier_with_validator.classify(invalid_input)


class TestLogging:
    """Test logging behavior."""

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_logs_start(self, mock_logger, classifier, sample_input):
        """Should log start of classification."""
        classifier.classify(sample_input)

        # Check for info log about starting
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("two-stage" in str(call) for call in info_calls)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_logs_stage_completion(self, mock_logger, classifier, sample_input):
        """Should log completion of each stage."""
        classifier.classify(sample_input)

        # Check for success logs
        success_calls = [call[0][0] for call in mock_logger.success.call_args_list]
        assert any("Stage 1" in str(call) for call in success_calls)
        assert any("Stage 2" in str(call) for call in success_calls)


class TestEdgeCases:
    """Test edge cases."""

    def test_classify_with_single_file(
        self, mock_llm_provider, mock_summary_prompt_builder, mock_summary_parser, mock_classification_prompt_builder, mock_classification_parser
    ):
        """Should handle single file input."""
        # Create a fresh classifier for single file test
        single_classifier = FileClassifier(
            llm_provider=mock_llm_provider,
            summary_prompt_builder=mock_summary_prompt_builder,
            summary_parser=mock_summary_parser,
            classification_prompt_builder=mock_classification_prompt_builder,
            classification_parser=mock_classification_parser,
        )

        # Reset the mock to only return one file
        mock_llm_provider.generate.side_effect = [
            '{"C:/test/single.txt": "單一"}',
            json.dumps({"C:/test/single.txt": {"category": "Single", "summary": "單一", "reason": "Single file"}}),
        ]

        mock_classification_parser.parse.return_value = {
            "C:/test/single.txt": FileMapping(
                old_path="C:/test/single.txt", new_relative_path="Single/single.txt", category="Single", summary="單一", reason="Single file"
            )
        }

        single_file = LLMInput(text=json.dumps({"C:/test/single.txt": "content"}))

        result = single_classifier.classify(single_file)

        assert result.metadata["file_count"] == 1

    def test_classify_with_unicode_content(self, classifier):
        """Should handle Unicode content."""
        unicode_files = {"C:/test/中文.txt": "這是中文內容", "C:/test/日本語.txt": "これは日本語です"}
        unicode_input = LLMInput(text=json.dumps(unicode_files, ensure_ascii=False))

        result = classifier.classify(unicode_input)

        assert result.metadata["file_count"] == 2
