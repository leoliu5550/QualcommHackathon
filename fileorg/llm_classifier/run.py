"""
Application Entry Point - Hexagonal Architecture

This module provides the main entry point and application services (use case implementations)
for the LLM Classifier system. It demonstrates dependency injection and orchestrates
the interaction between domain logic and infrastructure adapters.

SOLID Principles:
    - Dependency Inversion: All dependencies injected through ports
    - Single Responsibility: Each use case handles one workflow
    - Open/Closed: Can extend with new use cases without modifying existing code
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from fileorg.llm_classifier.ports import (
    ClassifyDocumentUseCase,
    RemapFoldersUseCase,
    ProcessFilesUseCase,
    ClassificationRequest,
    ClassificationResult,
    FolderMapping,
    ProcessingResult,
    FilePathMapping,
    LLMPort,
    PromptBuilderPort,
    OutputValidatorPort,
    ConfigPort,
    PersistencePort
)


# ============================================================================
# Application Services (Use Case Implementations)
# ============================================================================

class DocumentClassificationService(ClassifyDocumentUseCase):
    """
    Application service for document classification.

    Orchestrates the classification workflow using LLM and prompt building
    capabilities through ports.

    SOLID:
        - Single Responsibility: Only handles document classification workflow
        - Dependency Inversion: Depends on abstract ports, not concrete implementations
    """

    def __init__(
        self,
        llm: LLMPort,
        prompt_builder: PromptBuilderPort,
        validator: OutputValidatorPort
    ):
        """
        Initialize classification service with dependencies.

        Args:
            llm: LLM inference port
            prompt_builder: Prompt construction port
            validator: Output validation port
        """
        self.llm = llm
        self.prompt_builder = prompt_builder
        self.validator = validator

    def classify(self, request: ClassificationRequest) -> ClassificationResult:
        """
        Classify a document and return folder name.

        Args:
            request: Classification request with document content

        Returns:
            Classification result with folder name
        """
        # Build classification prompt
        messages = self.prompt_builder.build_classification_prompt(
            request.content,
            request.max_length
        )

        # Get LLM response
        raw_output = self.llm.generate(messages, max_tokens=200)

        # Validate and clean output
        is_valid, fixed_output = self.validator.validate_json(raw_output)
        if is_valid:
            raw_output = fixed_output

        # Sanitize folder name
        folder_name = self.validator.sanitize_folder_name(raw_output)

        return ClassificationResult(folder_name=folder_name)


class FolderRemappingService(RemapFoldersUseCase):
    """
    Application service for folder name remapping/grouping.

    Groups similar folder names to reduce redundancy and improve organization.
    """

    def __init__(
        self,
        llm: LLMPort,
        prompt_builder: PromptBuilderPort,
        validator: OutputValidatorPort
    ):
        """
        Initialize remapping service with dependencies.

        Args:
            llm: LLM inference port
            prompt_builder: Prompt construction port
            validator: Output validation port
        """
        self.llm = llm
        self.prompt_builder = prompt_builder
        self.validator = validator

    def remap(self, folder_names: List[str]) -> List[FolderMapping]:
        """
        Group similar folder names together.

        Args:
            folder_names: List of candidate folder names

        Returns:
            List of mappings from original to grouped folder names
        """
        if not folder_names:
            return []

        # Build remapping prompt
        messages = self.prompt_builder.build_remapping_prompt(folder_names)

        # Get LLM response
        raw_output = self.llm.generate(messages, max_tokens=400)

        # Parse and validate output
        mappings = self._parse_remapping_output(raw_output, folder_names)

        return mappings

    def _parse_remapping_output(
        self,
        output: str,
        original_folders: List[str]
    ) -> List[FolderMapping]:
        """
        Parse LLM output into folder mappings.

        Args:
            output: Raw LLM output
            original_folders: Original folder names for fallback

        Returns:
            List of folder mappings
        """
        try:
            # Try to fix JSON format
            if not output.startswith('['):
                output = '[{"foldername":"' + output
            if not output.endswith(']'):
                output = output.rstrip(',') + ']'

            data = json.loads(output)

            mappings = []
            for item in data:
                original = item["foldername"].lstrip('/')
                grouped = self.validator.sanitize_folder_name(item["groupname"])

                mappings.append(FolderMapping(
                    original_folder=original,
                    grouped_folder=grouped
                ))

            return mappings

        except (json.JSONDecodeError, KeyError) as e:
            print(f"JSON parsing failed: {e}\nOutput: {output}")
            # Fallback: use original names
            return [
                FolderMapping(
                    original_folder=folder,
                    grouped_folder=folder
                )
                for folder in original_folders
            ]


class FileProcessingService(ProcessFilesUseCase):
    """
    Application service for batch file processing.

    Orchestrates the complete workflow: classification → remapping → path generation.
    """

    def __init__(
        self,
        classifier: ClassifyDocumentUseCase,
        remapper: RemapFoldersUseCase,
        persistence: PersistencePort
    ):
        """
        Initialize file processing service.

        Args:
            classifier: Document classification use case
            remapper: Folder remapping use case
            persistence: Result persistence port
        """
        self.classifier = classifier
        self.remapper = remapper
        self.persistence = persistence

    def process(
        self,
        summaries_data: Dict[str, Any],
        base_output_dir: str = "./"
    ) -> ProcessingResult:
        """
        Process multiple files and generate organized structure.

        Args:
            summaries_data: Dictionary containing file summaries
            base_output_dir: Base directory for organized output

        Returns:
            Processing result with all mappings
        """
        summaries = summaries_data.get("summaries", [])

        # Step 1: Generate folder name for each file
        print("Step 1: Generating folder names for each file...")
        file_folder_mapping = []
        candidate_folders = []

        for summary_item in summaries:
            content = summary_item["summary"][:500]

            # Classify document
            request = ClassificationRequest(content=content, max_length=500)
            result = self.classifier.classify(request)

            file_folder_mapping.append({
                "original_path": summary_item["path"],
                "name": summary_item["name"],
                "initial_folder": result.folder_name
            })
            candidate_folders.append(result.folder_name)

        print(f"Initial folder names: {candidate_folders}")

        # Step 2: Group similar folder names together
        print("Step 2: Grouping similar folder names...")
        if len(candidate_folders) > 1:
            folder_mappings = self.remapper.remap(candidate_folders)
        else:
            folder_mappings = [
                FolderMapping(
                    original_folder=candidate_folders[0],
                    grouped_folder=candidate_folders[0]
                )
            ] if candidate_folders else []

        # Build folder name to group name mapping
        folder_to_group = {
            mapping.original_folder: mapping.grouped_folder
            for mapping in folder_mappings
        }

        # Step 3: Generate final file path mappings
        file_mappings = []

        for file_info in file_folder_mapping:
            file_name = file_info["name"]
            initial_folder = file_info["initial_folder"]

            # Find corresponding group name
            group_name = folder_to_group.get(initial_folder, initial_folder)

            # Build paths
            old_path = file_info["original_path"]
            new_path = os.path.join(base_output_dir, group_name, file_name)

            file_mappings.append(FilePathMapping(
                original_path=old_path,
                new_path=new_path
            ))

        result = ProcessingResult(
            file_mappings=file_mappings,
            folder_mappings=folder_mappings,
            stats={
                "total_files": len(summaries),
                "unique_folders": len(set(candidate_folders)),
                "consolidated_folders": len(set(folder_to_group.values()))
            }
        )

        return result


# ============================================================================
# Dependency Injection and Factory Functions
# ============================================================================

def create_classifier_system(config: Optional[ConfigPort] = None):
    """
    Create a fully wired classifier system using dependency injection.

    Args:
        config: Configuration port (creates default if None)

    Returns:
        Tuple of (classifier_service, remapper_service, processor_service)
    """
    # Create config if not provided
    if config is None:
        from fileorg.llm_classifier.adapters.config.file_config_adapter import get_config
        config = get_config()

    # Create adapters (infrastructure layer)
    from fileorg.llm_classifier.adapters.llm.factory import get_llm
    from fileorg.llm_classifier.adapters.prompt.builder_adapter import PromptBuilderAdapter
    from fileorg.llm_classifier.adapters.prompt.validator_adapter import OutputValidatorAdapter
    from fileorg.llm_classifier.adapters.persistence.json_adapter import JSONPersistenceAdapter

    llm = get_llm(
        backend=config.get("backend", "qualcomm"),
        **config.get_llm_config()
    )

    prompt_builder = PromptBuilderAdapter(
        version=config.get("prompt_version", "v2"),
        use_few_shot=config.get("use_few_shot", True),
        use_domain_detection=config.get("use_domain_detection", False)
    )

    validator = OutputValidatorAdapter()
    persistence = JSONPersistenceAdapter()

    # Create application services (use cases)
    classifier = DocumentClassificationService(llm, prompt_builder, validator)
    remapper = FolderRemappingService(llm, prompt_builder, validator)
    processor = FileProcessingService(classifier, remapper, persistence)

    return classifier, remapper, processor


def run_classification(
    summaries_data: Dict[str, Any],
    base_output_dir: str = "./",
    output_file: str = "file_mapping_result.json",
    config: Optional[ConfigPort] = None
) -> ProcessingResult:
    """
    Main entry point for running file classification.

    Args:
        summaries_data: Dictionary containing file summaries
        base_output_dir: Base directory for organized output
        output_file: Output JSON file path
        config: Optional configuration port

    Returns:
        Processing result
    """
    # Create system with dependency injection
    _, _, processor = create_classifier_system(config)

    # Process files
    result = processor.process(summaries_data, base_output_dir)

    # Save result
    from fileorg.llm_classifier.adapters.persistence.json_adapter import JSONPersistenceAdapter
    persistence = JSONPersistenceAdapter()
    persistence.save_result(result, output_file)

    return result


# ============================================================================
# Backward Compatibility Interface
# ============================================================================

class CreateFolderNamer:
    """
    Backward compatibility wrapper for legacy code.

    Provides the same interface as the old implementation while
    using the new hexagonal architecture underneath.
    """

    def __init__(
        self,
        use_advanced_prompt: bool = False,
        prompt_version: str = "v1",
        use_few_shot: bool = False,
        use_domain_detection: bool = False,
        config: dict = None
    ):
        """Initialize with legacy interface."""
        # Create config
        if config is None:
            from fileorg.llm_classifier.adapters.config.file_config_adapter import get_config
            cfg = get_config()
            config = cfg.get_llm_config()

        # Determine actual prompt version
        actual_version = prompt_version if use_advanced_prompt else "v1"

        # Create the new system
        from fileorg.llm_classifier.adapters.config.file_config_adapter import FileConfigAdapter
        config_port = FileConfigAdapter()
        config_port.update(
            **config,
            prompt_version=actual_version,
            use_few_shot=use_few_shot and use_advanced_prompt,
            use_domain_detection=use_domain_detection and use_advanced_prompt
        )

        self.classifier, self.remapper, self.processor = create_classifier_system(config_port)

    def create_folder_name(self, content: str) -> str:
        """Legacy interface for classification."""
        request = ClassificationRequest(content=content, max_length=500)
        result = self.classifier.classify(request)
        return result.folder_name

    def remapping_folder(self, candidate_folder: List[str]) -> List[Dict[str, str]]:
        """Legacy interface for remapping."""
        mappings = self.remapper.remap(candidate_folder)
        return [
            {
                "foldername": m.original_folder,
                "groupname": m.grouped_folder
            }
            for m in mappings
        ]

    def process_files(
        self,
        summaries_data: Dict[str, Any],
        base_output_dir: str = "./"
    ) -> Dict[str, List[Dict[str, str]]]:
        """Legacy interface for processing."""
        result = self.processor.process(summaries_data, base_output_dir)
        return {
            "file_paths": [
                {"original": m.original_path, "new": m.new_path}
                for m in result.file_mappings
            ]
        }

    def save_result(
        self,
        result: Dict[str, Any],
        output_file: str = "file_mapping_result.json"
    ):
        """Legacy interface for saving."""
        from fileorg.llm_classifier.adapters.persistence.json_adapter import JSONPersistenceAdapter
        persistence = JSONPersistenceAdapter()

        # Convert legacy format to new format
        file_mappings = [
            FilePathMapping(
                original_path=item["original"],
                new_path=item["new"]
            )
            for item in result.get("file_paths", [])
        ]

        processing_result = ProcessingResult(
            file_mappings=file_mappings,
            folder_mappings=[],
            stats=result.get("stats")
        )

        persistence.save_result(processing_result, output_file)

    def clean_output(self, text: str) -> str:
        """Legacy interface for cleaning."""
        from fileorg.llm_classifier.adapters.prompt.validator_adapter import OutputValidatorAdapter
        validator = OutputValidatorAdapter()
        return validator.sanitize_folder_name(text)


if __name__ == "__main__":
    # Example usage
    print("LLM Classifier - Hexagonal Architecture")
    print("=" * 50)
    print("\nThis module provides the application services and entry point.")
    print("Import and use the functions above for classification tasks.")
