"""
Unit tests for FileClassifier use case.

Tests verify that FileClassifier correctly implements the IClassifierUseCase
interface and properly orchestrates the file classification workflow.
"""

import json
from unittest.mock import Mock, patch

import pytest

from fileorg.llm_classifier.application.file_classifier import FileClassifier
from fileorg.llm_classifier.ports import IClassifierUseCase
from fileorg.llm_classifier.ports.models import (
    ClassificationOutput,
    FileMapping,
    LLMInput,
)


@pytest.fixture
def mock_llm_provider():
    """Provide a mock LLM provider."""
    provider = Mock()
    provider.__class__.__name__ = "MockLLMProvider"
    provider.generate.return_value = '{"category1": ["file1.txt"], "category2": ["file2.txt"]}'
    return provider


@pytest.fixture
def mock_prompt_builder():
    """Provide a mock prompt builder."""
    builder = Mock()
    builder.__class__.__name__ = "MockPromptBuilder"
    builder.build_prompt.return_value = [{"role": "system", "content": "You are a classifier"}, {"role": "user", "content": "Classify these files"}]
    return builder


@pytest.fixture
def mock_output_parser():
    """Provide a mock output parser."""
    parser = Mock()
    parser.__class__.__name__ = "MockOutputParser"
    parser.parse.return_value = {
        "C:/test/file1.txt": FileMapping(
            old_path="C:/test/file1.txt", new_relative_path="Category1/file1.txt", category="Category1", summary="Test file 1", reason="Test reason 1"
        )
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
def classifier(mock_llm_provider, mock_prompt_builder, mock_output_parser):
    """Provide a FileClassifier with mocked dependencies."""
    return FileClassifier(llm_provider=mock_llm_provider, prompt_builder=mock_prompt_builder, output_parser=mock_output_parser)


@pytest.fixture
def classifier_with_validator(mock_llm_provider, mock_prompt_builder, mock_output_parser, mock_validator):
    """Provide a FileClassifier with validator."""
    return FileClassifier(
        llm_provider=mock_llm_provider, prompt_builder=mock_prompt_builder, output_parser=mock_output_parser, validator=mock_validator
    )


@pytest.fixture
def sample_input():
    """Provide sample LLM input."""
    files_dict = {"C:/test/file1.txt": "Sample content 1", "C:/test/file2.txt": "Sample content 2"}
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


class TestInitialization:
    """Test FileClassifier initialization."""

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_initialization_with_all_dependencies(self, mock_logger, mock_llm_provider, mock_prompt_builder, mock_output_parser, mock_validator):
        """Should initialize with all dependencies and custom instruction."""
        custom_instruction = "Custom classification instruction"

        classifier = FileClassifier(
            llm_provider=mock_llm_provider,
            prompt_builder=mock_prompt_builder,
            output_parser=mock_output_parser,
            validator=mock_validator,
            instruction=custom_instruction,
        )

        assert classifier.llm_provider is mock_llm_provider
        assert classifier.prompt_builder is mock_prompt_builder
        assert classifier.output_parser is mock_output_parser
        assert classifier.validator is mock_validator
        assert classifier.instruction == custom_instruction

        # Verify logger was called
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "MockLLMProvider" in log_message
        assert "MockPromptBuilder" in log_message
        assert "MockOutputParser" in log_message
        assert "with validator" in log_message

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_initialization_without_validator(self, mock_logger, mock_llm_provider, mock_prompt_builder, mock_output_parser):
        """Should initialize without validator."""
        classifier = FileClassifier(llm_provider=mock_llm_provider, prompt_builder=mock_prompt_builder, output_parser=mock_output_parser)

        assert classifier.validator is None

        log_message = mock_logger.info.call_args[0][0]
        assert "no validator" in log_message

    def test_initialization_with_default_instruction(self, mock_llm_provider, mock_prompt_builder, mock_output_parser):
        """Should use default instruction when not provided."""
        classifier = FileClassifier(llm_provider=mock_llm_provider, prompt_builder=mock_prompt_builder, output_parser=mock_output_parser)

        assert classifier.instruction is not None
        assert "請根據以下檔案的內容和路徑" in classifier.instruction
        assert "Please classify" in classifier.instruction


class TestGetDefaultInstruction:
    """Test default instruction generation."""

    def test_default_instruction_content(self, classifier):
        """Should return correct default instruction."""
        instruction = classifier._get_default_instruction()

        assert isinstance(instruction, str)
        assert len(instruction) > 0
        assert "請根據以下檔案的內容和路徑" in instruction
        assert "Please classify the following files" in instruction
        assert "JSON" in instruction


class TestValidateWithValidator:
    """Test input validation with validator."""

    def test_validate_empty_text_raises_error(self, classifier_with_validator):
        """Should raise ValueError for empty text."""
        empty_input = LLMInput(text="")

        with pytest.raises(ValueError, match="Input text cannot be empty"):
            classifier_with_validator._validate_with_validator(empty_input)

    def test_validate_whitespace_only_raises_error(self, classifier_with_validator):
        """Should raise ValueError for whitespace-only text."""
        whitespace_input = LLMInput(text="   \n\t  ")

        with pytest.raises(ValueError, match="Input text cannot be empty"):
            classifier_with_validator._validate_with_validator(whitespace_input)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_validate_valid_json_paths_dict(self, mock_logger, classifier_with_validator):
        """Should pass validation for valid JSON paths dictionary."""
        files_dict = {"C:/test/file1.txt": "content1", "C:/test/file2.txt": "content2"}
        valid_input = LLMInput(text=json.dumps(files_dict))

        # Should not raise
        classifier_with_validator._validate_with_validator(valid_input)

        # Verify validator was called
        classifier_with_validator.validator.validate_paths_dict.assert_called_once()
        mock_logger.debug.assert_called_with("Input validation passed")

    def test_validate_invalid_json_paths_dict_raises_error(self, classifier_with_validator):
        """Should raise ValueError for invalid paths dictionary."""
        files_dict = {
            "C:/test/file1.txt": "content1",
            "invalid_path": "content2",  # Not absolute
        }
        invalid_input = LLMInput(text=json.dumps(files_dict))

        # Make validator reject this
        classifier_with_validator.validator.validate_paths_dict.return_value = False

        with pytest.raises(ValueError, match="Invalid file paths or content in input"):
            classifier_with_validator._validate_with_validator(invalid_input)

    def test_validate_non_json_falls_back_to_text_validation(self, classifier_with_validator):
        """Should fall back to text validation for non-JSON input."""
        non_json_input = LLMInput(text="This is plain text, not JSON")

        # Make text validation pass
        classifier_with_validator.validator.validate.return_value = True

        # Should not raise
        classifier_with_validator._validate_with_validator(non_json_input)

        # Verify text validator was called
        classifier_with_validator.validator.validate.assert_called_once_with("This is plain text, not JSON")

    def test_validate_non_json_fails_text_validation_raises_error(self, classifier_with_validator):
        """Should raise ValueError when non-JSON input fails text validation."""
        non_json_input = LLMInput(text="Invalid text")

        # Make text validation fail
        classifier_with_validator.validator.validate.return_value = False

        with pytest.raises(ValueError, match="Input text validation failed"):
            classifier_with_validator._validate_with_validator(non_json_input)


class TestClassifyMethod:
    """Test the main classify method."""

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_successful_workflow(self, mock_logger, classifier, sample_input, mock_output_parser):
        """Should successfully classify files through complete workflow."""
        result = classifier.classify(sample_input)

        # Verify result structure
        assert isinstance(result, ClassificationOutput)
        assert isinstance(result.path_mappings, dict)
        assert len(result.path_mappings) > 0
        assert result.raw_response is not None
        assert result.metadata is not None

        # Verify metadata
        assert result.metadata["input_length"] == len(sample_input.text)
        assert result.metadata["max_tokens"] == sample_input.max_tokens
        assert result.metadata["file_count"] == len(result.path_mappings)

        # Verify all dependencies were called
        classifier.prompt_builder.build_prompt.assert_called_once()
        classifier.llm_provider.generate.assert_called_once()
        classifier.output_parser.parse.assert_called_once()

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_with_validator(self, mock_logger, classifier_with_validator, sample_input):
        """Should use validator when provided."""
        result = classifier_with_validator.classify(sample_input)

        # Verify validator was called
        classifier_with_validator.validator.validate_paths_dict.assert_called_once()

        # Verify result
        assert isinstance(result, ClassificationOutput)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_without_validator(self, mock_logger, classifier, sample_input):
        """Should skip validation when no validator provided."""
        result = classifier.classify(sample_input)

        # Verify result (no validator calls to check)
        assert isinstance(result, ClassificationOutput)

    def test_classify_empty_input_without_validator_raises_error(self, classifier):
        """Should raise ValueError for empty input when no validator."""
        empty_input = LLMInput(text="")

        with pytest.raises(ValueError, match="Input text cannot be empty"):
            classifier.classify(empty_input)

    def test_classify_whitespace_input_without_validator_raises_error(self, classifier):
        """Should raise ValueError for whitespace-only input when no validator."""
        whitespace_input = LLMInput(text="   \n\t  ")

        with pytest.raises(ValueError, match="Input text cannot be empty"):
            classifier.classify(whitespace_input)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_calls_prompt_builder_with_correct_args(self, mock_logger, classifier, sample_input):
        """Should call prompt builder with correct arguments."""
        classifier.classify(sample_input)

        classifier.prompt_builder.build_prompt.assert_called_once_with(
            text=sample_input.text, instruction=classifier.instruction, max_tokens=sample_input.max_tokens
        )

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_calls_llm_provider_with_correct_args(self, mock_logger, classifier, sample_input):
        """Should call LLM provider with prompt messages and max_tokens."""
        classifier.classify(sample_input)

        # Get the messages from prompt_builder
        expected_messages = classifier.prompt_builder.build_prompt.return_value

        classifier.llm_provider.generate.assert_called_once_with(messages=expected_messages, max_tokens=sample_input.max_tokens)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_calls_output_parser_with_llm_response(self, mock_logger, classifier, sample_input):
        """Should call output parser with LLM response."""
        classifier.classify(sample_input)

        # Get the LLM response
        expected_response = classifier.llm_provider.generate.return_value

        classifier.output_parser.parse.assert_called_once_with(expected_response)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_includes_raw_response_in_output(self, mock_logger, classifier, sample_input):
        """Should include raw LLM response in output."""
        result = classifier.classify(sample_input)

        expected_raw_response = classifier.llm_provider.generate.return_value
        assert result.raw_response == expected_raw_response

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_custom_max_tokens(self, mock_logger, classifier):
        """Should respect custom max_tokens."""
        custom_input = LLMInput(text='{"C:/test/file.txt": "content"}', max_tokens=1024)

        classifier.classify(custom_input)

        # Verify max_tokens was passed correctly
        classifier.prompt_builder.build_prompt.assert_called_with(text=custom_input.text, instruction=classifier.instruction, max_tokens=1024)
        classifier.llm_provider.generate.assert_called_with(messages=classifier.prompt_builder.build_prompt.return_value, max_tokens=1024)


class TestClassifyErrorHandling:
    """Test error handling in classify method."""

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_validation_error_propagates(self, mock_logger, classifier_with_validator, sample_input):
        """Should propagate ValueError from validation."""
        # Make validator raise error
        classifier_with_validator.validator.validate_paths_dict.return_value = False

        with pytest.raises(ValueError, match="Invalid file paths"):
            classifier_with_validator.classify(sample_input)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_llm_generation_error_propagates(self, mock_logger, classifier, sample_input):
        """Should propagate RuntimeError from LLM generation."""
        # Make LLM provider raise error
        classifier.llm_provider.generate.side_effect = RuntimeError("LLM generation failed")

        with pytest.raises(RuntimeError, match="LLM generation failed"):
            classifier.classify(sample_input)

        # Verify error was logged
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        assert "LLM generation error" in error_message

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_parsing_error_propagates(self, mock_logger, classifier, sample_input):
        """Should propagate ValueError from output parsing."""
        # Make parser raise error
        classifier.output_parser.parse.side_effect = ValueError("Invalid JSON format")

        with pytest.raises(ValueError, match="Invalid JSON format"):
            classifier.classify(sample_input)

        # Verify error was logged
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        assert "Validation or parsing error" in error_message

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_unexpected_error_wrapped_as_runtime_error(self, mock_logger, classifier, sample_input):
        """Should wrap unexpected errors as RuntimeError."""
        # Make prompt builder raise unexpected error
        classifier.prompt_builder.build_prompt.side_effect = Exception("Unexpected error")

        with pytest.raises(RuntimeError, match="Classification failed: Unexpected error"):
            classifier.classify(sample_input)

        # Verify error was logged
        mock_logger.error.assert_called()
        error_message = mock_logger.error.call_args[0][0]
        assert "Unexpected error during classification" in error_message


class TestClassifyLogging:
    """Test logging behavior in classify method."""

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_logs_start(self, mock_logger, classifier, sample_input):
        """Should log classification start with max_tokens."""
        classifier.classify(sample_input)

        # Find the info call with "Starting file classification"
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        start_log = [msg for msg in info_calls if "Starting file classification" in msg]
        assert len(start_log) > 0
        assert f"max_tokens={sample_input.max_tokens}" in start_log[0]

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_logs_prompt_building(self, mock_logger, classifier, sample_input):
        """Should log prompt building step."""
        classifier.classify(sample_input)

        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Building prompt" in msg for msg in debug_calls)
        assert any("Prompt built" in msg for msg in debug_calls)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_logs_llm_call(self, mock_logger, classifier, sample_input):
        """Should log LLM provider call."""
        classifier.classify(sample_input)

        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Calling LLM provider" in msg for msg in debug_calls)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_logs_generation_success(self, mock_logger, classifier, sample_input):
        """Should log successful LLM generation."""
        classifier.classify(sample_input)

        success_calls = [call[0][0] for call in mock_logger.success.call_args_list]
        assert any("LLM generation completed" in msg for msg in success_calls)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_logs_parsing(self, mock_logger, classifier, sample_input):
        """Should log output parsing step."""
        classifier.classify(sample_input)

        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Parsing LLM output" in msg for msg in debug_calls)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_logs_final_success(self, mock_logger, classifier, sample_input):
        """Should log final success with mapping count."""
        result = classifier.classify(sample_input)

        success_calls = [call[0][0] for call in mock_logger.success.call_args_list]
        parsed_log = [msg for msg in success_calls if "Parsed" in msg and "path mappings" in msg]
        assert len(parsed_log) > 0
        assert f"Parsed {len(result.path_mappings)} path mappings" in parsed_log[0]


class TestClassifyMetadata:
    """Test metadata generation in classify output."""

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_metadata_includes_input_length(self, mock_logger, classifier, sample_input):
        """Should include input text length in metadata."""
        result = classifier.classify(sample_input)

        assert "input_length" in result.metadata
        assert result.metadata["input_length"] == len(sample_input.text)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_metadata_includes_output_length(self, mock_logger, classifier, sample_input):
        """Should include output text length in metadata."""
        result = classifier.classify(sample_input)

        assert "output_length" in result.metadata
        assert result.metadata["output_length"] == len(result.raw_response)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_metadata_includes_max_tokens(self, mock_logger, classifier, sample_input):
        """Should include max_tokens in metadata."""
        result = classifier.classify(sample_input)

        assert "max_tokens" in result.metadata
        assert result.metadata["max_tokens"] == sample_input.max_tokens

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_metadata_includes_file_count(self, mock_logger, classifier, sample_input):
        """Should include file count in metadata."""
        result = classifier.classify(sample_input)

        assert "file_count" in result.metadata
        assert result.metadata["file_count"] == len(result.path_mappings)


class TestEdgeCases:
    """Test edge cases and complex scenarios."""

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_with_large_input(self, mock_logger, classifier):
        """Should handle large input text."""
        large_files = {f"C:/test/file{i}.txt": f"content{i}" * 100 for i in range(100)}
        large_input = LLMInput(text=json.dumps(large_files))

        result = classifier.classify(large_input)

        assert isinstance(result, ClassificationOutput)
        assert result.metadata["input_length"] == len(large_input.text)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_with_unicode_content(self, mock_logger, classifier):
        """Should handle Unicode in file paths and content."""
        unicode_files = {"C:/測試/文件.txt": "中文內容", "C:/тест/файл.txt": "русский текст"}
        unicode_input = LLMInput(text=json.dumps(unicode_files, ensure_ascii=False))

        result = classifier.classify(unicode_input)

        assert isinstance(result, ClassificationOutput)

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_preserves_custom_instruction(self, mock_logger, mock_llm_provider, mock_prompt_builder, mock_output_parser):
        """Should use custom instruction when provided."""
        custom_instruction = "分類這些檔案到特定的資料夾"

        classifier = FileClassifier(
            llm_provider=mock_llm_provider, prompt_builder=mock_prompt_builder, output_parser=mock_output_parser, instruction=custom_instruction
        )

        sample_input = LLMInput(text='{"C:/test/file.txt": "content"}')
        classifier.classify(sample_input)

        # Verify custom instruction was used
        mock_prompt_builder.build_prompt.assert_called_once()
        call_kwargs = mock_prompt_builder.build_prompt.call_args
        assert call_kwargs[1]["instruction"] == custom_instruction

    @patch("fileorg.llm_classifier.application.file_classifier.logger")
    def test_classify_with_empty_parser_result(self, mock_logger, classifier, sample_input):
        """Should handle empty result from parser."""
        classifier.output_parser.parse.return_value = {}

        result = classifier.classify(sample_input)

        assert isinstance(result, ClassificationOutput)
        assert len(result.path_mappings) == 0
        assert result.metadata["file_count"] == 0
