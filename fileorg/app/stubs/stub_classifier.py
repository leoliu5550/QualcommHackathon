"""
Stub LLM Classifier for MVP demonstration.

This is a minimal stub implementation that classifies files into simple
categories based on file extensions. Replace with actual Task3 LLM
classifier when available.
"""

from pathlib import Path
from typing import Dict

from loguru import logger

from fileorg.file_ops.ports.parser_ports import MultiParserOutput
from fileorg.llm_classifier.ports.models import (
    ClassificationOutput,
    FileMapping,
)


class StubLLMClassifier:
    """
    Stub classifier that categorizes files by extension.

    This stub provides minimal classification logic for MVP demonstration:
    - PDF → "Documents"
    - DOCX/PPTX → "Office_Files"
    - JPG/PNG → "Images"
    - TXT/CSV → "Text_Files"
    - Others → "Miscellaneous"

    Usage:
        classifier = StubLLMClassifier()
        classification_output = classifier.classify(multi_parser_output)
    """

    # Simple category mapping based on file extensions
    CATEGORY_MAP = {
        ".pdf": "Documents",
        ".docx": "Office_Files",
        ".pptx": "Office_Files",
        ".xlsx": "Office_Files",
        ".jpg": "Images",
        ".jpeg": "Images",
        ".png": "Images",
        ".gif": "Images",
        ".txt": "Text_Files",
        ".csv": "Text_Files",
        ".md": "Text_Files",
    }

    def classify(
        self,
        multi_parser_output: MultiParserOutput,
        root_dir: str,
    ) -> ClassificationOutput:
        """
        Classify files based on extension (stub implementation).

        Converts MultiParserOutput (Dict[path, content]) into ClassificationOutput
        with FileMapping objects.

        Args:
            multi_parser_output: Parsed file contents from Task2
            root_dir: Original root directory (for logging)

        Returns:
            ClassificationOutput with path_mappings

        Note:
            This is a STUB implementation. Real Task3 implementation will:
            - Use LLM to analyze file content
            - Generate intelligent summaries
            - Provide detailed classification reasoning
            - Support custom categories
        """
        logger.info(f"[STUB] Classifying {len(multi_parser_output)} files by extension")

        path_mappings: Dict[str, FileMapping] = {}

        for file_path, content in multi_parser_output.items():
            # Get file extension
            path_obj = Path(file_path)
            extension = path_obj.suffix.lower()
            filename = path_obj.name

            # Determine category
            category = self.CATEGORY_MAP.get(extension, "Miscellaneous")

            # Create stub summary (first 100 chars of content or file info)
            if content and len(content.strip()) > 0:
                summary = f"{filename}: {content[:100].strip()}..."
            else:
                summary = f"{filename} (empty or binary file)"

            # Create stub reason
            reason = f"File extension '{extension}' maps to category '{category}'"

            # Create new_relative_path: Category/filename
            new_relative_path = f"{category}/{filename}"

            # Create FileMapping
            file_mapping = FileMapping(
                old_path=file_path,
                new_relative_path=new_relative_path,
                category=category,
                summary=summary,
                reason=reason,
            )

            path_mappings[file_path] = file_mapping

        # Create classification output
        classification_output = ClassificationOutput(
            path_mappings=path_mappings,
            raw_response="[STUB] No LLM response - using extension-based classification",
            metadata={
                "total_files": len(path_mappings),
                "stub": True,
                "categories": list({m.category for m in path_mappings.values()}),
            },
        )

        logger.info(f"[STUB] Classification complete: {len(path_mappings)} files into {len(classification_output.metadata['categories'])} categories")

        return classification_output
