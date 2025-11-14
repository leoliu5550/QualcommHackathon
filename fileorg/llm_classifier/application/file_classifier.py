"""
File classification use case implementation with two-stage LLM processing.

This module implements the core file classification logic:
- Stage 1: Extract keywords from each file independently
- Stage 2: Classify all files based on extracted keywords
"""

import json
import time
from typing import Dict, Optional

from loguru import logger

from fileorg.llm_classifier.ports.interfaces import (
    IClassifierUseCase,
    ILLMProvider,
    IOutputParser,
    IPromptBuilder,
    ISummaryParser,
    ITextValidator,
)
from fileorg.llm_classifier.ports.models import ClassificationOutput, FileSummary, LLMInput


class FileClassifier(IClassifierUseCase):
    """
    Two-stage file classification use case.

    Implements two-stage LLM processing for improved accuracy:
    1. Stage 1: Extract 1-2 word keywords from each file (reduces token usage)
    2. Stage 2: Classify files into categories based on keywords

    Generic Design:
        All dependencies are injected as interfaces (ports), making this class:
        - Agnostic to specific LLM providers (GPU, MPS, QAIC, TURU, etc.)
        - Agnostic to specific prompt strategies (can use different templates)
        - Agnostic to specific output formats (different parsers)

    Example:
        >>> # Using GPU provider
        >>> classifier = FileClassifier(
        ...     llm_provider=GPUProvider(),
        ...     summary_prompt_builder=SummaryPromptBuilder(...),
        ...     summary_parser=SummaryOutputParser(),
        ...     classification_prompt_builder=ClassificationPromptBuilder(...),
        ...     classification_parser=PathMappingOutputParser(),
        ... )
        >>>
        >>> # Using TURU provider (just swap the provider!)
        >>> classifier = FileClassifier(
        ...     llm_provider=TURUProvider(base_url="..."),
        ...     # ... same other dependencies
        ... )
        >>>
        >>> files = {"/path/report.pdf": "Q4 earnings..."}
        >>> result = classifier.classify(LLMInput(text=json.dumps(files)))
    """

    def __init__(
        self,
        llm_provider: ILLMProvider,
        summary_prompt_builder: IPromptBuilder,
        summary_parser: ISummaryParser,
        classification_prompt_builder: IPromptBuilder,
        classification_parser: IOutputParser,
        validator: Optional[ITextValidator] = None,
    ):
        """
        Initialize file classifier with dependency injection.

        Design Rationale:
            All dependencies are interfaces (ports), following Dependency Inversion Principle.
            This makes the class:
            - Testable: Can inject mocks for testing
            - Flexible: Can swap implementations at runtime
            - Maintainable: Changes to adapters don't affect this class

        Args:
            llm_provider: LLM inference provider (any implementation of ILLMProvider)
            summary_prompt_builder: Prompt builder for Stage 1 keyword extraction
            summary_parser: Parser for Stage 1 output (keywords)
            classification_prompt_builder: Prompt builder for Stage 2 classification
            classification_parser: Parser for Stage 2 output (file mappings)
            validator: Optional text/path validator (ITextValidator)

        Note:
            All concrete adapters are injected from outside, not created here.
            This follows the "Don't call us, we'll call you" principle (Hollywood Principle).
        """
        # Port dependencies (all interfaces, no concrete classes)
        self.llm_provider = llm_provider
        self.summary_prompt_builder = summary_prompt_builder
        self.summary_parser = summary_parser
        self.classification_prompt_builder = classification_prompt_builder
        self.classification_parser = classification_parser
        self.validator = validator

        logger.info(
            f"Initialized FileClassifier (two-stage) with "
            f"provider={llm_provider.__class__.__name__}, "
            f"validator={'enabled' if validator else 'disabled'}"
        )

    def classify(self, input_data: LLMInput) -> ClassificationOutput:
        """
        Classify files using two-stage LLM processing.

        This is the main use case method that orchestrates the entire classification workflow.

        Workflow:
            1. Validate input
            2. Stage 1: Generate keywords for each file (generate_summaries)
            3. Stage 2: Classify files based on keywords (classify_by_summaries)
            4. Return structured output with metadata

        Args:
            input_data: LLMInput containing JSON-formatted file data
                       Format: {"absolute_path": "content", ...}

        Returns:
            ClassificationOutput with:
            - path_mappings: Dict[path, FileMapping] with classification results
            - raw_responses: Dict with "stage1_summaries" and "stage2_classification"
            - metadata: Processing statistics (time, token usage, etc.)

        Raises:
            ValueError: If input validation fails
            RuntimeError: If LLM generation or parsing fails

        Design Note:
            This method only orchestrates the workflow, delegating actual work
            to specialized methods (Single Responsibility Principle).
        """
        # Step 1: Validate input
        self._validate_input(input_data)

        logger.info("Starting two-stage file classification")
        start_time = time.time()

        try:
            # Step 2: Stage 1 - Generate keywords for each file
            summaries, stage1_raw = self.generate_summaries(input_data)
            stage1_time = time.time() - start_time
            logger.success(f"Stage 1 completed in {stage1_time:.2f}s: {len(summaries)} keywords extracted")

            # Step 3: Stage 2 - Classify files based on keywords
            stage2_start = time.time()
            path_mappings, stage2_raw = self.classify_by_summaries(summaries, input_data.max_tokens)
            stage2_time = time.time() - stage2_start
            logger.success(f"Stage 2 completed in {stage2_time:.2f}s: {len(path_mappings)} files classified")

            # Step 4: Return combined output with metadata
            total_time = time.time() - start_time
            return ClassificationOutput(
                path_mappings=path_mappings,
                raw_responses={
                    "stage1_summaries": stage1_raw,
                    "stage2_classification": stage2_raw,
                },
                metadata={
                    "file_count": len(path_mappings),
                    "stage1_time_ms": int(stage1_time * 1000),
                    "stage2_time_ms": int(stage2_time * 1000),
                    "total_time_ms": int(total_time * 1000),
                    "max_tokens": input_data.max_tokens,
                },
            )

        except Exception as e:
            logger.error(f"Two-stage classification failed: {e}")
            raise

    def generate_summaries(self, input_data: LLMInput) -> tuple[Dict[str, FileSummary], str]:
        """
        Stage 1: Generate keywords for each file independently.

        Why Stage 1 is needed:
            - Reduces token usage: Keywords are much shorter than full content
            - Improves accuracy: LLM focuses on extracting key information first
            - Enables batch processing: All keywords fit in one Stage 2 prompt

        Process:
            For each file:
            1. Build prompt using summary_prompt_builder
            2. Generate keyword using llm_provider
            3. Parse keyword using summary_parser

        Args:
            input_data: LLMInput containing file contents
                       Format: {"absolute_path": "content", ...}

        Returns:
            Tuple of (summaries_dict, combined_raw_response):
            - summaries_dict: Dict[file_path, FileSummary] with extracted keywords
            - combined_raw_response: All raw LLM outputs concatenated (for debugging)

        Raises:
            RuntimeError: If LLM generation or parsing fails

        Design Note:
            This method is generic - it works with any IPromptBuilder and ISummaryParser.
            Different prompt strategies can be used by injecting different builders.
        """
        logger.debug("Stage 1: Generating keywords for each file")

        # Parse input files first to catch JSON errors early
        try:
            files = json.loads(input_data.text)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON input: {e}")
            raise ValueError(f"Input text must be valid JSON format: {e}") from e

        try:
            # Process each file independently
            summaries = {}
            raw_responses = []

            for file_path, content in files.items():
                # Build single-file input
                single_file_input = json.dumps({file_path: content}, ensure_ascii=False)

                # Build prompt for keyword extraction
                # Note: The prompt builder decides the actual prompt format
                prompt_messages = self.summary_prompt_builder.build_prompt(
                    text=single_file_input,
                    instruction=("Extract 1-2 word keywords that best describe this file's content. Focus on the main topic or category."),
                    max_tokens=input_data.max_tokens,
                )

                # Generate keyword using LLM
                # Note: Works with any ILLMProvider (GPU, TURU, MPS, etc.)
                raw_response = self.llm_provider.generate(
                    messages=prompt_messages,
                    max_tokens=input_data.max_tokens,
                )
                raw_responses.append(raw_response)

                # Parse keyword into FileSummary
                # Note: The parser decides how to extract the keyword
                summary = self.summary_parser.parse(
                    text=raw_response,
                    file_path=file_path,
                    raw_length=len(raw_response),
                )
                summaries[file_path] = summary

                # Use repr() to avoid UnicodeEncodeError on Windows console
                logger.debug(f"Extracted keyword for {file_path}: {repr(summary.summary)}")

            # Combine all raw responses for debugging/logging
            combined_raw = "\n---\n".join(raw_responses)

            logger.info(f"Stage 1 complete: {len(summaries)} keywords extracted")
            return summaries, combined_raw

        except Exception as e:
            logger.error(f"Stage 1 (keyword extraction) failed: {e}")
            raise RuntimeError(f"Keyword extraction failed: {e}") from e

    def classify_by_summaries(self, summaries: Dict[str, FileSummary], max_tokens: int = 150000) -> tuple[Dict[str, any], str]:
        """
        Stage 2: Classify files based on their keywords.

        Why Stage 2 is needed:
            - Holistic view: LLM sees all files' keywords together
            - Consistent categories: Ensures related files go to same category
            - Better accuracy: Classification based on extracted key information

        Process:
            1. Build classification prompt with all keywords
            2. Generate classification using llm_provider
            3. Parse into FileMapping objects using classification_parser

        Args:
            summaries: Dict mapping file paths to FileSummary objects
            max_tokens: Maximum tokens for LLM input

        Returns:
            Tuple of (path_mappings, raw_response):
            - path_mappings: Dict[file_path, FileMapping] with classification results
            - raw_response: Raw LLM output from Stage 2 (for debugging)

        Raises:
            RuntimeError: If LLM generation or parsing fails

        Design Note:
            This method is generic - it works with any IPromptBuilder and IOutputParser.
            The actual classification logic is determined by the injected adapters.
        """
        logger.debug("Stage 2: Classifying files based on keywords")

        try:
            # Build keyword dict: {file_path: keyword}
            keyword_dict = {path: summary.summary for path, summary in summaries.items()}
            keyword_json = json.dumps(keyword_dict, ensure_ascii=False)

            # Build classification prompt
            # Note: The prompt builder decides the actual prompt format
            prompt_messages = self.classification_prompt_builder.build_prompt(
                text=keyword_json,
                instruction=(
                    "Classify these files into categories based on their keywords. "
                    "Provide category name, keep the keyword as summary, and explain the reason."
                ),
                max_tokens=max_tokens,
            )

            # Generate classification using LLM
            # Note: Works with any ILLMProvider (GPU, TURU, MPS, etc.)
            raw_response = self.llm_provider.generate(
                messages=prompt_messages,
                max_tokens=max_tokens,
            )

            # Parse into path mappings
            # Note: The parser decides how to extract and structure the results
            path_mappings = self.classification_parser.parse(raw_response)

            logger.info(f"Stage 2 complete: {len(path_mappings)} files classified")
            return path_mappings, raw_response

        except Exception as e:
            logger.error(f"Stage 2 (classification) failed: {e}")
            raise RuntimeError(f"Classification failed: {e}") from e

    def _validate_input(self, input_data: LLMInput) -> None:
        """
        Validate input data before processing.

        Args:
            input_data: Input data to validate

        Raises:
            ValueError: If validation fails

        Design Note:
            Validation logic is delegated to the validator (if provided).
            This follows Single Responsibility Principle.
        """
        if not input_data.text or not input_data.text.strip():
            raise ValueError("Input text cannot be empty")

        if self.validator:
            try:
                files_dict = json.loads(input_data.text)
                if not self.validator.validate_paths_dict(files_dict):
                    raise ValueError("Invalid file paths in input. Ensure all keys are absolute paths.")
            except json.JSONDecodeError as err:
                if not self.validator.validate(input_data.text):
                    raise ValueError("Input text validation failed") from err

            logger.debug("Input validation passed")
