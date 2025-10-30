"""
JSON Persistence Adapter

This adapter implements PersistencePort for storing and loading processing
results in JSON format.

SOLID Principles:
    - Single Responsibility: Only handles JSON file persistence
    - Open/Closed: Can be extended with other formats (XML, YAML) via new adapters
    - Liskov Substitution: Can replace any PersistencePort implementation
    - Dependency Inversion: Implements the abstract PersistencePort
"""

import json
from typing import Dict, Any
from fileorg.llm_classifier.ports import (
    PersistencePort,
    ProcessingResult,
    FilePathMapping,
    FolderMapping
)


class JSONPersistenceAdapter(PersistencePort):
    """
    Adapter for JSON-based persistence of processing results.

    Handles serialization and deserialization of processing results
    to/from JSON files with proper encoding for international characters.

    Attributes:
        encoding: File encoding to use (default: 'utf-8')
    """

    def __init__(self, encoding: str = 'utf-8'):
        """
        Initialize JSON persistence adapter.

        Args:
            encoding: Character encoding for file operations
        """
        self.encoding = encoding

    def save_result(
        self,
        result: ProcessingResult,
        output_file: str
    ) -> None:
        """
        Save processing results to JSON file.

        Args:
            result: Processing result to save
            output_file: Output file path

        Raises:
            IOError: If file cannot be written
        """
        # Convert dataclass to dictionary
        data = {
            "file_paths": [
                {
                    "original": mapping.original_path,
                    "new": mapping.new_path
                }
                for mapping in result.file_mappings
            ],
            "folder_mappings": [
                {
                    "foldername": mapping.original_folder,
                    "groupname": mapping.grouped_folder
                }
                for mapping in result.folder_mappings
            ]
        }

        # Add statistics if available
        if result.stats:
            data["stats"] = result.stats

        # Write to file with proper encoding
        with open(output_file, 'w', encoding=self.encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Results saved to: {output_file}")

    def load_result(self, input_file: str) -> ProcessingResult:
        """
        Load processing results from JSON file.

        Args:
            input_file: Input file path

        Returns:
            Loaded processing result

        Raises:
            IOError: If file cannot be read
            ValueError: If JSON is malformed
        """
        with open(input_file, 'r', encoding=self.encoding) as f:
            data = json.load(f)

        # Reconstruct file path mappings
        file_mappings = [
            FilePathMapping(
                original_path=item["original"],
                new_path=item["new"]
            )
            for item in data.get("file_paths", [])
        ]

        # Reconstruct folder mappings
        folder_mappings = [
            FolderMapping(
                original_folder=item["foldername"],
                grouped_folder=item["groupname"]
            )
            for item in data.get("folder_mappings", [])
        ]

        # Get statistics if available
        stats = data.get("stats")

        return ProcessingResult(
            file_mappings=file_mappings,
            folder_mappings=folder_mappings,
            stats=stats
        )
