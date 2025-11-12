"""
File classification use case implementation.

This module implements the core file classification logic by orchestrating
the prompt builder and LLM provider components.

Supports two scenarios:
1. File Grouping (v1): Group files into categories
2. Path Mapping (v2): Map files to organized paths
"""

import json
from typing import Optional

from loguru import logger

from fileorg.llm_classifier.ports.interfaces import (
    IClassifierUseCase,
    ILLMProvider,
    IOutputParser,
    IPromptBuilder,
    ITextValidator,
)
from fileorg.llm_classifier.ports.models import ClassificationOutput, LLMInput


class FileClassifier(IClassifierUseCase):
    """
    File classification use case using LLM.

    Maps files to organized path structure based on content analysis.

    Workflow:
    1. Validate input (with optional validator)
    2. Build prompt from file data using IPromptBuilder
    3. Generate LLM response using ILLMProvider
    4. Parse output to path mappings using IOutputParser
    5. Return structured path mapping results

    Example:
        >>> from fileorg.llm_classifier.adapters import GPUProvider
        >>> from fileorg.llm_classifier.adapters.prompt_builder import LlamaPromptBuilder
        >>> from fileorg.llm_classifier.application.path_mapping_output_parser import PathMappingOutputParser
        >>> from fileorg.llm_classifier.application.text_validator import BasicTextValidator
        >>>
        >>> classifier = FileClassifier(
        ...     llm_provider=GPUProvider(),
        ...     prompt_builder=LlamaPromptBuilder(...),
        ...     output_parser=PathMappingOutputParser(),
        ...     validator=BasicTextValidator()
        ... )
        >>>
        >>> files = {"/path/to/report.pdf": "Q4 earnings report content..."}
        >>> result = classifier.classify(LLMInput(text=json.dumps(files)))
        >>> print(result.path_mappings)  # {"C:/Desktop/report.pdf": FileMapping(...)}
    """

    def __init__(
        self,
        llm_provider: ILLMProvider,
        prompt_builder: IPromptBuilder,
        output_parser: IOutputParser,
        validator: Optional[ITextValidator] = None,
        instruction: Optional[str] = None,
    ):
        """
        Initialize file classifier.

        Args:
            llm_provider: LLM inference provider (e.g., GPUProvider)
            prompt_builder: Prompt builder (e.g., LlamaPromptBuilder)
            output_parser: Output parser (e.g., PathMappingOutputParser)
            validator: Optional text/path validator (recommended for path validation)
            instruction: Custom classification instruction (uses default if None)
        """
        self.llm_provider = llm_provider
        self.prompt_builder = prompt_builder
        self.output_parser = output_parser
        self.validator = validator
        self.instruction = instruction or self._get_default_instruction()

        logger.info(
            f"Initialized FileClassifier with {llm_provider.__class__.__name__}, "
            f"{prompt_builder.__class__.__name__}, "
            f"{output_parser.__class__.__name__}, "
            f"{'with validator' if validator else 'no validator'}"
        )

    def _get_default_instruction(self) -> str:
        """Get default classification instruction."""
        return (
            "請根據以下檔案的內容和路徑，將它們分類到適當的資料夾中。"
            "請提供建議的資料夾結構，以JSON格式回傳。\n\n"
            "Please classify the following files based on their content and paths. "
            "Provide a suggested folder structure in JSON format."
        )

    def _validate_with_validator(self, input_data: LLMInput) -> None:
        """
        Validate input using the validator.

        For path mapping scenarios, validates path format and structure.

        Args:
            input_data: Input data to validate

        Raises:
            ValueError: If validation fails
        """
        if not input_data.text or not input_data.text.strip():
            raise ValueError("Input text cannot be empty")

        # Try to parse as JSON for path validation
        try:
            files_dict = json.loads(input_data.text)
            if not self.validator.validate_paths_dict(files_dict):
                raise ValueError("Invalid file paths or content in input. Ensure all keys are absolute paths.")
        except json.JSONDecodeError as err:
            # If not JSON, fall back to basic text validation
            if not self.validator.validate(input_data.text):
                raise ValueError("Input text validation failed") from err

        logger.debug("Input validation passed")

    def classify(self, input_data: LLMInput) -> ClassificationOutput:
        """
        Classify files and map to organized paths using LLM.

        Args:
            input_data: LLMInput containing JSON-formatted file data
                       Format: {"absolute_path": "content", ...}

        Returns:
            ClassificationOutput with path mappings

        Raises:
            ValueError: If input validation fails
            RuntimeError: If LLM generation fails
        """
        # Step 1: Validate input
        if self.validator:
            self._validate_with_validator(input_data)
        else:
            if not input_data.text or not input_data.text.strip():
                raise ValueError("Input text cannot be empty")

        logger.info(f"Starting file classification with max_tokens={input_data.max_tokens}")

        try:
            # Step 2: Build prompt
            logger.debug("Building prompt...")
            prompt_messages = self.prompt_builder.build_prompt(text=input_data.text, instruction=self.instruction, max_tokens=input_data.max_tokens)

            logger.debug(f"Prompt built: {len(prompt_messages)} messages")

            # Step 3: Generate LLM response
            logger.debug("Calling LLM provider...")
            raw_response = self.llm_provider.generate(messages=prompt_messages, max_tokens=input_data.max_tokens)

            logger.success(f"LLM generation completed: {len(raw_response)} characters")

            # Step 4: Parse output to path mappings
            logger.debug("Parsing LLM output to path mappings...")
            path_mappings = self.output_parser.parse(raw_response)
            logger.success(f"Parsed {len(path_mappings)} path mappings")

            # Step 5: Return output
            return ClassificationOutput(
                path_mappings=path_mappings,
                raw_response=raw_response,
                metadata={
                    "input_length": len(input_data.text),
                    "output_length": len(raw_response),
                    "max_tokens": input_data.max_tokens,
                    "file_count": len(path_mappings),
                },
            )

        except ValueError as e:
            logger.error(f"Validation or parsing error: {e}")
            raise
        except RuntimeError as e:
            logger.error(f"LLM generation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during classification: {e}")
            raise RuntimeError(f"Classification failed: {e}") from e
