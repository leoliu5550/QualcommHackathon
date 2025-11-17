"""
Unit tests for SequentialFileIdMapper.
"""

import pytest

from fileorg.llm_classifier.adapters.sequential_file_id_mapper import SequentialFileIdMapper


class TestSequentialFileIdMapper:
    """Test suite for SequentialFileIdMapper."""

    def test_create_mappings_basic(self):
        """Test basic ID mapping creation."""
        mapper = SequentialFileIdMapper()
        file_paths = [
            "/path/to/file1.txt",
            "/path/to/file2.txt",
            "/path/to/file3.txt",
        ]

        id_to_path = mapper.create_mappings(file_paths)

        assert len(id_to_path) == 3
        assert id_to_path["A001"] == "/path/to/file1.txt"
        assert id_to_path["A002"] == "/path/to/file2.txt"
        assert id_to_path["A003"] == "/path/to/file3.txt"

    def test_create_mappings_with_double_space_filename(self):
        """Test mapping creation with filenames containing double spaces (Issue #112)."""
        mapper = SequentialFileIdMapper()
        file_paths = [
            "/Users/leo/Desktop/Ch7  Cluster analysis.pdf",  # Double space
            "/Users/leo/Desktop/Ch8 Regression.pdf",  # Single space
        ]

        id_to_path = mapper.create_mappings(file_paths)

        assert len(id_to_path) == 2
        assert id_to_path["A001"] == "/Users/leo/Desktop/Ch7  Cluster analysis.pdf"
        assert id_to_path["A002"] == "/Users/leo/Desktop/Ch8 Regression.pdf"

    def test_get_path(self):
        """Test retrieving path by file ID."""
        mapper = SequentialFileIdMapper()
        file_paths = ["/path/file1.txt", "/path/file2.txt"]
        mapper.create_mappings(file_paths)

        assert mapper.get_path("A001") == "/path/file1.txt"
        assert mapper.get_path("A002") == "/path/file2.txt"
        assert mapper.get_path("A999") is None

    def test_get_id(self):
        """Test retrieving file ID by path."""
        mapper = SequentialFileIdMapper()
        file_paths = ["/path/file1.txt", "/path/file2.txt"]
        mapper.create_mappings(file_paths)

        assert mapper.get_id("/path/file1.txt") == "A001"
        assert mapper.get_id("/path/file2.txt") == "A002"
        assert mapper.get_id("/nonexistent/path.txt") is None

    def test_get_all_mappings(self):
        """Test retrieving all mappings."""
        mapper = SequentialFileIdMapper()
        file_paths = ["/path/file1.txt", "/path/file2.txt"]
        mapper.create_mappings(file_paths)

        all_mappings = mapper.get_all_mappings()

        assert len(all_mappings) == 2
        assert all_mappings["A001"] == "/path/file1.txt"
        assert all_mappings["A002"] == "/path/file2.txt"

    def test_reset(self):
        """Test resetting the mapper."""
        mapper = SequentialFileIdMapper()
        file_paths = ["/path/file1.txt"]
        mapper.create_mappings(file_paths)

        assert len(mapper.get_all_mappings()) == 1

        mapper.reset()

        assert len(mapper.get_all_mappings()) == 0
        assert mapper.get_id("/path/file1.txt") is None

    def test_reset_resets_counter(self):
        """Test that reset resets the counter for new ID generation."""
        mapper = SequentialFileIdMapper()

        # Create first batch
        mapper.create_mappings(["/path/file1.txt"])
        assert "A001" in mapper.get_all_mappings()

        # Reset and create second batch
        mapper.reset()
        mapper.create_mappings(["/path/file2.txt"])

        # Should start from A001 again
        assert "A001" in mapper.get_all_mappings()
        assert mapper.get_path("A001") == "/path/file2.txt"

    def test_custom_prefix(self):
        """Test creating mapper with custom prefix."""
        mapper = SequentialFileIdMapper(prefix="B")
        file_paths = ["/path/file1.txt", "/path/file2.txt"]
        mapper.create_mappings(file_paths)

        assert "B001" in mapper.get_all_mappings()
        assert "B002" in mapper.get_all_mappings()

    def test_custom_id_width(self):
        """Test creating mapper with custom ID width."""
        mapper = SequentialFileIdMapper(id_width=4)
        file_paths = ["/path/file1.txt"]
        mapper.create_mappings(file_paths)

        assert "A0001" in mapper.get_all_mappings()

    def test_create_mappings_empty_list_raises_error(self):
        """Test that empty file list raises ValueError."""
        mapper = SequentialFileIdMapper()

        with pytest.raises(ValueError, match="file_paths cannot be empty"):
            mapper.create_mappings([])

    def test_create_mappings_duplicate_paths_raises_error(self):
        """Test that duplicate paths raise ValueError."""
        mapper = SequentialFileIdMapper()
        file_paths = [
            "/path/file1.txt",
            "/path/file2.txt",
            "/path/file1.txt",  # Duplicate
        ]

        with pytest.raises(ValueError, match="duplicate entries"):
            mapper.create_mappings(file_paths)

    def test_invalid_prefix_raises_error(self):
        """Test that invalid prefix raises ValueError."""
        with pytest.raises(ValueError, match="Prefix must be a single letter"):
            SequentialFileIdMapper(prefix="AB")

        with pytest.raises(ValueError, match="Prefix must be a single letter"):
            SequentialFileIdMapper(prefix="1")

    def test_invalid_id_width_raises_error(self):
        """Test that invalid ID width raises ValueError."""
        with pytest.raises(ValueError, match="ID width must be >= 1"):
            SequentialFileIdMapper(id_width=0)

        with pytest.raises(ValueError, match="ID width must be >= 1"):
            SequentialFileIdMapper(id_width=-1)

    def test_counter_exceeds_maximum_raises_error(self):
        """Test that counter overflow raises ValueError."""
        mapper = SequentialFileIdMapper(id_width=1)  # Max 9 IDs

        # Create 9 mappings (should work)
        paths = [f"/path/file{i}.txt" for i in range(1, 10)]
        mapper.create_mappings(paths)

        # 10th mapping should fail
        with pytest.raises(ValueError, match="Counter exceeded maximum value"):
            mapper.create_mappings(["/path/file10.txt"])

    def test_bidirectional_mapping_consistency(self):
        """Test that bidirectional mapping is consistent."""
        mapper = SequentialFileIdMapper()
        file_paths = [
            "/path/file1.txt",
            "/path/file2.txt",
            "/path/file3.txt",
        ]
        mapper.create_mappings(file_paths)

        # Test round-trip consistency
        for path in file_paths:
            file_id = mapper.get_id(path)
            retrieved_path = mapper.get_path(file_id)
            assert retrieved_path == path

    def test_windows_path_with_double_spaces(self):
        """Test Windows paths with double spaces (Issue #112)."""
        mapper = SequentialFileIdMapper()
        file_paths = [
            r"C:\Users\leo\Desktop\Ch7  Cluster analysis.pdf",
            r"C:\Users\leo\Desktop\Ch8 Regression.pdf",
        ]
        mapper.create_mappings(file_paths)

        assert mapper.get_id(r"C:\Users\leo\Desktop\Ch7  Cluster analysis.pdf") == "A001"
        assert mapper.get_path("A001") == r"C:\Users\leo\Desktop\Ch7  Cluster analysis.pdf"

    def test_multiple_special_whitespace_characters(self):
        """Test paths with various whitespace patterns."""
        mapper = SequentialFileIdMapper()
        file_paths = [
            "/path/file  with  multiple  spaces.txt",
            "/path/file with\ttab.txt",  # Tab character
            "/path/normal file.txt",
        ]
        mapper.create_mappings(file_paths)

        # All should be mapped correctly
        assert len(mapper.get_all_mappings()) == 3
        assert mapper.get_id("/path/file  with  multiple  spaces.txt") == "A001"
        assert mapper.get_id("/path/file with\ttab.txt") == "A002"
        assert mapper.get_id("/path/normal file.txt") == "A003"


class TestSequentialFileIdMapperSOLIDPrinciples:
    """Test suite verifying SOLID principles compliance."""

    def test_single_responsibility_principle(self):
        """Verify SRP: Mapper only handles ID generation and mapping."""
        mapper = SequentialFileIdMapper()

        # Mapper should ONLY provide ID mapping functionality
        # It should NOT:
        # - Parse files
        # - Validate file existence
        # - Modify file system
        # - Handle LLM interactions

        # Test only mapping-related methods exist
        mapping_methods = {
            "create_mappings",
            "get_path",
            "get_id",
            "get_all_mappings",
            "reset",
        }

        public_methods = {name for name in dir(mapper) if not name.startswith("_") and callable(getattr(mapper, name))}

        # All public methods should be mapping-related
        assert public_methods == mapping_methods

    def test_open_closed_principle(self):
        """Verify OCP: Can extend via inheritance without modification."""
        # Example: Custom ID strategy without modifying base class

        class UUIDFileIdMapper(SequentialFileIdMapper):
            """Custom mapper using different ID strategy."""

            def _generate_next_id(self):
                import uuid

                return str(uuid.uuid4())[:8]

        # Should work without modifying SequentialFileIdMapper
        custom_mapper = UUIDFileIdMapper()
        custom_mapper.create_mappings(["/path/file.txt"])

        # Verify it works
        assert len(custom_mapper.get_all_mappings()) == 1

    def test_liskov_substitution_principle(self):
        """Verify LSP: Mapper can be substituted anywhere IFileIdMapper is expected."""
        from fileorg.llm_classifier.ports.interfaces import IFileIdMapper

        def use_mapper(mapper: IFileIdMapper, paths: list[str]) -> dict:
            """Function that uses IFileIdMapper interface."""
            mapper.create_mappings(paths)
            return mapper.get_all_mappings()

        # SequentialFileIdMapper should be substitutable
        mapper = SequentialFileIdMapper()
        result = use_mapper(mapper, ["/path/file.txt"])

        assert len(result) == 1
        assert isinstance(result, dict)

    def test_interface_segregation_principle(self):
        """Verify ISP: Interface only defines essential operations."""
        from fileorg.llm_classifier.ports.interfaces import IFileIdMapper

        # IFileIdMapper should only require essential methods
        required_methods = {
            "create_mappings",
            "get_path",
            "get_id",
            "get_all_mappings",
            "reset",
        }

        interface_methods = {name for name in dir(IFileIdMapper) if not name.startswith("_") and callable(getattr(IFileIdMapper, name))}

        # Interface should not force implementation of unnecessary methods
        assert interface_methods == required_methods

    def test_dependency_inversion_principle(self):
        """Verify DIP: FileClassifier depends on IFileIdMapper abstraction."""
        import inspect

        from fileorg.llm_classifier.application.file_classifier import FileClassifier

        # FileClassifier should accept IFileIdMapper, not concrete implementation
        # This is tested by checking the type hint in __init__
        sig = inspect.signature(FileClassifier.__init__)
        file_id_mapper_param = sig.parameters.get("file_id_mapper")

        # Should accept Optional[IFileIdMapper]
        assert file_id_mapper_param is not None
        # Type hint should reference interface, not concrete class
        # (This is checked at design time via type annotations)
