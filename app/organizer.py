"""
AI Filing System - Main Organizer Application

This module integrates all tasks (Task1-Task5) to provide a complete
file organization pipeline:

1. Task1: Scan files (FileScanner)
2. Task2: Parse file contents (ParseFileClient)
3. Task3: Classify files using LLM (Stub for now)
4. Task4: Create restoration point (RestorationUseCase)
5. Task5: Execute file organization (FileOrganizationUseCase)

Usage:
    organizer = FileOrganizer()
    result = organizer.organize(
        source_dir="C:/Documents",
        target_dir="C:/Organized",
        dry_run=True
    )
"""

import json
from pathlib import Path
from typing import Optional

from loguru import logger

from fileorg.file_ops.adapters.parser_factory_adapter import ParserFactoryAdapter
from fileorg.file_ops.adapters.scanner import FileScanner
from fileorg.file_ops.application.parser_client import ParseFileClient
from fileorg.file_organizer.adapters.local_file_organizer import LocalFileOrganizer
from fileorg.file_organizer.application.file_organization_use_case import (
    FileOrganizationUseCase,
)
from fileorg.file_organizer.ports import ExecutionResult
from fileorg.llm_classifier.ports.models import (
    ClassificationOutput,
    FileMapping,
    LLMInput,
)
from fileorg.restoration.adapters.json_restoration_manager import (
    JsonRestorationManager,
)
from fileorg.restoration.application.restoration_use_case import RestorationUseCase


class StubLLMClassifier:
    """
    Stub classifier for Task3.

    Provides simple rule-based classification until real LLM integration is ready.
    Groups files by extension into basic categories.
    """

    CATEGORY_MAP = {
        # Documents
        ".pdf": "Documents/PDFs",
        ".doc": "Documents/Word",
        ".docx": "Documents/Word",
        ".txt": "Documents/Text",
        ".md": "Documents/Markdown",
        # Spreadsheets
        ".xlsx": "Spreadsheets/Excel",
        ".xls": "Spreadsheets/Excel",
        ".csv": "Spreadsheets/CSV",
        # Images
        ".jpg": "Images/Photos",
        ".jpeg": "Images/Photos",
        ".png": "Images/Graphics",
        ".gif": "Images/Graphics",
        # Code
        ".py": "Code/Python",
        ".js": "Code/JavaScript",
        ".ts": "Code/TypeScript",
        ".java": "Code/Java",
        # Archives
        ".zip": "Archives/Compressed",
        ".rar": "Archives/Compressed",
        ".7z": "Archives/Compressed",
        # Default
        "default": "Miscellaneous/Other",
    }

    def classify(self, input_data: LLMInput) -> ClassificationOutput:
        """
        Stub classification based on file extensions.

        Args:
            input_data: LLMInput containing JSON of {path: content}

        Returns:
            ClassificationOutput with simple extension-based mappings
        """
        logger.info("[STUB] Using stub classifier (extension-based)")

        # Parse input
        try:
            files_dict = json.loads(input_data.text)
        except json.JSONDecodeError:
            logger.error("Failed to parse input as JSON")
            return ClassificationOutput(path_mappings={}, raw_response="Error: Invalid input format", metadata={"error": "Invalid JSON input"})

        # Generate path mappings
        path_mappings = {}
        for file_path, _content in files_dict.items():
            path_obj = Path(file_path)
            extension = path_obj.suffix.lower()

            # Get category
            category = self.CATEGORY_MAP.get(extension, self.CATEGORY_MAP["default"])
            category_name = category.split("/")[0]  # e.g., "Documents"

            # Build new relative path
            new_relative_path = f"{category}/{path_obj.name}"

            # Create mapping
            mapping = FileMapping(
                old_path=file_path,
                new_relative_path=new_relative_path,
                category=category_name,
                summary=f"File type: {extension or 'unknown'}",
                reason=f"Classified by extension: {extension}",
            )

            path_mappings[file_path] = mapping

        logger.success(f"[STUB] Generated {len(path_mappings)} mappings")

        return ClassificationOutput(
            path_mappings=path_mappings,
            raw_response=f"Stub classification: {len(path_mappings)} files categorized",
            metadata={"stub": True, "file_count": len(path_mappings), "method": "extension-based"},
        )


class FileOrganizer:
    """
    Main file organization orchestrator.

    Integrates all tasks into a complete pipeline.

    Example:
        >>> organizer = FileOrganizer()
        >>>
        >>> # Preview organization
        >>> result = organizer.organize(
        ...     source_dir="C:/Documents",
        ...     target_dir="C:/Organized",
        ...     dry_run=True
        ... )
        >>> print(f"Would organize {result.total_count} files")
        >>>
        >>> # Execute organization
        >>> result = organizer.organize(
        ...     source_dir="C:/Documents",
        ...     target_dir="C:/Organized",
        ...     dry_run=False
        ... )
        >>> print(f"Organized {result.success_count}/{result.total_count} files")
    """

    def __init__(self, use_stub_classifier: bool = True):
        """
        Initialize the file organizer with all required components.

        Args:
            use_stub_classifier: If True, use stub classifier; else would need real LLM setup
        """
        # Task1: Scanner
        self.scanner = None  # Created per-run with source_dir

        # Task2: Parser
        self.parser_factory = ParserFactoryAdapter()
        self.parser_client = ParseFileClient(self.parser_factory, char_limit=500)

        # Task3: Classifier
        if use_stub_classifier:
            self.classifier = StubLLMClassifier()
            logger.info("Using stub classifier (extension-based)")
        else:
            # TODO: Initialize real LLM classifier when ready
            raise NotImplementedError("Real LLM classifier not yet implemented")

        # Task4: Restoration
        self.restoration_manager = JsonRestorationManager()
        self.restoration_use_case = RestorationUseCase(self.restoration_manager)

        # Task5: File Organizer
        self.file_executor = LocalFileOrganizer(self.restoration_manager)
        self.organization_use_case = FileOrganizationUseCase(self.file_executor)

    def organize(
        self,
        source_dir: str,
        target_dir: str,
        dry_run: bool = False,
        create_restoration_point: bool = True,
        ignore_patterns: Optional[list[str]] = None,
    ) -> ExecutionResult:
        """
        Execute the complete file organization pipeline.

        Pipeline:
        1. Scan source directory for files
        2. Parse file contents
        3. Classify files using LLM (or stub)
        4. [Optional] Create restoration point
        5. Execute file organization

        Args:
            source_dir: Source directory to scan and organize
            target_dir: Target directory for organized files
            dry_run: If True, preview without actual file movement
            create_restoration_point: Whether to create restoration point (ignored if dry_run)
            ignore_patterns: Optional file patterns to ignore during scanning

        Returns:
            ExecutionResult with detailed operation statistics

        Example:
            >>> result = organizer.organize(
            ...     source_dir="C:/Users/user/Downloads",
            ...     target_dir="C:/Users/user/Organized",
            ...     dry_run=True
            ... )
            >>> for op in result.operations:
            ...     print(f"{op.old_path} -> {op.new_path}")
        """
        logger.info("=" * 80)
        logger.info("Starting File Organization Pipeline")
        logger.info("=" * 80)
        logger.info(f"Source: {source_dir}")
        logger.info(f"Target: {target_dir}")
        logger.info(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")
        logger.info("=" * 80)

        # Validate directories
        source_path = Path(source_dir).resolve()
        target_path = Path(target_dir).resolve()

        if not source_path.exists():
            raise FileNotFoundError(f"Source directory does not exist: {source_dir}")
        if not source_path.is_dir():
            raise NotADirectoryError(f"Source path is not a directory: {source_dir}")

        # Step 1: Scan files (Task1)
        logger.info("[Task1] Scanning files...")
        scanner = FileScanner(str(source_path), ignore_patterns=ignore_patterns)
        scan_report = scanner.generate_report()
        logger.success(f"[Task1] Found {scan_report['file_count']} files")

        if scan_report["file_count"] == 0:
            logger.warning("No files to organize")
            return ExecutionResult(
                total_count=0,
                success_count=0,
                failed_count=0,
                skipped_count=0,
                operations=[],
                restoration_manifest_path=None,
                execution_time=0.0,
            )

        # Step 2: Parse file contents (Task2)
        logger.info("[Task2] Parsing file contents...")
        parsed_files = self.parser_client.parse_multiple(scan_report)
        logger.success(f"[Task2] Parsed {len(parsed_files)} files")

        # Prepare input for classifier (convert to JSON)
        files_dict = dict(parsed_files.items())
        classifier_input = LLMInput(text=json.dumps(files_dict, ensure_ascii=False), max_tokens=150000)

        # Step 3: Classify files (Task3)
        logger.info("[Task3] Classifying files...")
        classification_output = self.classifier.classify(classifier_input)
        logger.success(f"[Task3] Generated {len(classification_output.path_mappings)} classifications")

        # Step 4 & 5: Execute organization with restoration (Task4 + Task5)
        logger.info("[Task5] Executing file organization...")
        result = self.organization_use_case.organize_files(
            classification_output=classification_output,
            target_dir=str(target_path),
            root_dir=str(source_path),
            dry_run=dry_run,
            create_restoration_point=create_restoration_point and not dry_run,
        )

        # Summary
        logger.info("=" * 80)
        logger.info("Pipeline Complete")
        logger.info("=" * 80)
        logger.info(f"Total files: {result.total_count}")
        logger.info(f"Success: {result.success_count}")
        logger.info(f"Failed: {result.failed_count}")
        logger.info(f"Skipped: {result.skipped_count}")
        logger.info(f"Time: {result.execution_time:.2f}s")
        if result.restoration_manifest_path:
            logger.info(f"Restoration manifest: {result.restoration_manifest_path}")
        logger.info("=" * 80)

        return result

    def preview(
        self,
        source_dir: str,
        target_dir: str,
        ignore_patterns: Optional[list[str]] = None,
    ) -> ExecutionResult:
        """
        Preview file organization without executing.

        Convenience method that runs organize with dry_run=True.

        Args:
            source_dir: Source directory to scan
            target_dir: Target directory for organized files
            ignore_patterns: Optional file patterns to ignore

        Returns:
            ExecutionResult showing planned operations
        """
        logger.info("Running preview mode (dry-run)")
        return self.organize(
            source_dir=source_dir,
            target_dir=target_dir,
            dry_run=True,
            create_restoration_point=False,
            ignore_patterns=ignore_patterns,
        )


def main():
    """Example usage of FileOrganizer."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m app.organizer <source_dir> <target_dir> [--execute]")
        print("  --execute: Actually move files (default is dry-run)")
        sys.exit(1)

    source_dir = sys.argv[1]
    target_dir = sys.argv[2]
    execute = "--execute" in sys.argv

    # Initialize organizer
    organizer = FileOrganizer(use_stub_classifier=True)

    # Run organization
    result = organizer.organize(
        source_dir=source_dir,
        target_dir=target_dir,
        dry_run=not execute,
        create_restoration_point=True,
    )

    # Display results
    print("\n" + "=" * 80)
    print("Organization Results")
    print("=" * 80)
    print(f"Total: {result.total_count}")
    print(f"Success: {result.success_count}")
    print(f"Failed: {result.failed_count}")
    print(f"Skipped: {result.skipped_count}")

    if result.failed_count > 0:
        print("\nFailed operations:")
        for op in result.operations:
            if op.status == "failed":
                print(f"  - {op.old_path}: {op.error}")

    if result.restoration_manifest_path:
        print(f"\nRestoration manifest: {result.restoration_manifest_path}")
        print("To undo: python -m fileorg.restoration.cli restore <manifest_path>")


if __name__ == "__main__":
    main()
