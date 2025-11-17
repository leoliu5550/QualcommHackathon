"""
Sequential File ID Mapper - SOLID Implementation

This module implements the IFileIdMapper interface using a simple sequential
ID generation scheme (A001, A002, A003...).
"""

from typing import Dict, List, Optional

from fileorg.llm_classifier.ports.interfaces import IFileIdMapper


class SequentialFileIdMapper(IFileIdMapper):
    """
    Sequential file ID mapper using A001, A002, A003... format.

    This implementation provides a simple, predictable ID scheme that:
    - Is short and readable (better for LLM token efficiency)
    - Is sortable (maintains file order)
    - Has minimal collision risk within a single session
    - Is deterministic for the same input order

    Thread Safety: Not thread-safe. Create separate instances for concurrent use.

    Usage:
        # Initialize mapper
        mapper = SequentialFileIdMapper()

        # Create mappings for files
        file_paths = [
            "/Users/leo/Desktop/Ch7  Cluster analysis.pdf",  # Note: double space
            "/Users/leo/Desktop/Ch8 Regression.pdf"
        ]
        id_to_path = mapper.create_mappings(file_paths)
        # Result: {
        #     "A001": "/Users/leo/Desktop/Ch7  Cluster analysis.pdf",
        #     "A002": "/Users/leo/Desktop/Ch8 Regression.pdf"
        # }

        # Retrieve path by ID
        path = mapper.get_path("A001")
        # "/Users/leo/Desktop/Ch7  Cluster analysis.pdf"

        # Retrieve ID by path
        file_id = mapper.get_id("/Users/leo/Desktop/Ch7  Cluster analysis.pdf")
        # "A001"

        # Reset for new batch
        mapper.reset()

    Attributes:
        _id_to_path: Internal mapping from file ID to file path
        _path_to_id: Internal reverse mapping from file path to file ID
        _counter: Current ID counter for sequential generation
        _prefix: ID prefix (default: "A")
        _id_width: Zero-padding width for ID numbers (default: 3)
    """

    def __init__(self, prefix: str = "A", id_width: int = 3):
        """
        Initialize the sequential file ID mapper.

        Args:
            prefix: Letter prefix for IDs (default: "A")
            id_width: Number of digits in ID (default: 3 for A001-A999)

        Raises:
            ValueError: If prefix is not a single letter or id_width < 1
        """
        if not prefix.isalpha() or len(prefix) != 1:
            raise ValueError(f"Prefix must be a single letter, got: {prefix}")
        if id_width < 1:
            raise ValueError(f"ID width must be >= 1, got: {id_width}")

        self._prefix = prefix.upper()
        self._id_width = id_width
        self._counter = 0
        self._id_to_path: Dict[str, str] = {}
        self._path_to_id: Dict[str, str] = {}

    def create_mappings(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Create ID mappings for a list of file paths.

        This method generates sequential IDs (A001, A002, ...) for each file path
        in the order provided. Duplicate paths are rejected.

        Args:
            file_paths: List of absolute file paths to map

        Returns:
            Dictionary mapping file IDs to original paths
            Example: {"A001": "/path/file1.txt", "A002": "/path/file2.txt"}

        Raises:
            ValueError: If file_paths is empty or contains duplicates
        """
        if not file_paths:
            raise ValueError("file_paths cannot be empty")

        # Check for duplicates
        if len(file_paths) != len(set(file_paths)):
            duplicates = [path for path in file_paths if file_paths.count(path) > 1]
            raise ValueError(f"file_paths contains duplicate entries: {set(duplicates)}")

        # Generate IDs sequentially
        for file_path in file_paths:
            file_id = self._generate_next_id()
            self._id_to_path[file_id] = file_path
            self._path_to_id[file_path] = file_id

        return self._id_to_path.copy()

    def get_path(self, file_id: str) -> Optional[str]:
        """
        Retrieve original file path for a given file ID.

        Args:
            file_id: The file identifier (e.g., "A001")

        Returns:
            Original file path if found, None otherwise

        Examples:
            >>> mapper = SequentialFileIdMapper()
            >>> mapper.create_mappings(["/path/file.txt"])
            >>> mapper.get_path("A001")
            "/path/file.txt"
            >>> mapper.get_path("A999")
            None
        """
        return self._id_to_path.get(file_id)

    def get_id(self, file_path: str) -> Optional[str]:
        """
        Retrieve file ID for a given file path.

        Args:
            file_path: The absolute file path

        Returns:
            File ID if found, None otherwise

        Examples:
            >>> mapper = SequentialFileIdMapper()
            >>> mapper.create_mappings(["/path/file.txt"])
            >>> mapper.get_id("/path/file.txt")
            "A001"
            >>> mapper.get_id("/nonexistent/path.txt")
            None
        """
        return self._path_to_id.get(file_path)

    def get_all_mappings(self) -> Dict[str, str]:
        """
        Get all current ID-to-path mappings.

        Returns:
            Dictionary of all current mappings {file_id: file_path}

        Examples:
            >>> mapper = SequentialFileIdMapper()
            >>> mapper.create_mappings(["/path/file1.txt", "/path/file2.txt"])
            >>> mapper.get_all_mappings()
            {"A001": "/path/file1.txt", "A002": "/path/file2.txt"}
        """
        return self._id_to_path.copy()

    def reset(self) -> None:
        """
        Clear all mappings and reset internal state.

        This method is useful for processing new batches of files in the same
        session without creating a new mapper instance.

        Examples:
            >>> mapper = SequentialFileIdMapper()
            >>> mapper.create_mappings(["/path/file1.txt"])
            >>> len(mapper.get_all_mappings())
            1
            >>> mapper.reset()
            >>> len(mapper.get_all_mappings())
            0
        """
        self._counter = 0
        self._id_to_path.clear()
        self._path_to_id.clear()

    def _generate_next_id(self) -> str:
        """
        Generate the next sequential file ID.

        Internal method for creating IDs in format: {prefix}{counter:0{width}d}
        Example: A001, A002, A003...

        Returns:
            Next sequential file ID

        Raises:
            ValueError: If counter exceeds maximum value for the given width
        """
        max_value = 10**self._id_width - 1
        if self._counter >= max_value:
            raise ValueError(
                f"Counter exceeded maximum value {max_value} for ID width {self._id_width}. Consider using a larger id_width or resetting the mapper."
            )

        self._counter += 1
        file_id = f"{self._prefix}{self._counter:0{self._id_width}d}"
        return file_id
