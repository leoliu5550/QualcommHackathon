"""Core functionality tests for restoration module."""

import json
from pathlib import Path

import pytest

from fileorg.restoration.adapters import JsonRestorationManager
from fileorg.restoration.application import RestorationUseCase
from fileorg.restoration.ports import FileOperation, RestorationPoint


class TestDataclasses:
    """Test dataclass initialization and basic functionality."""

    def test_file_operation_creation(self):
        """Test FileOperation dataclass creation."""
        op = FileOperation(
            old_path="C:/source/file.pdf",
            new_path="C:/target/Documents/file.pdf",
            category="Documents",
        )
        assert op.old_path == "C:/source/file.pdf"
        assert op.new_path == "C:/target/Documents/file.pdf"
        assert op.category == "Documents"
        assert op.executed is False
        assert op.error is None

    def test_file_operation_update_status(self):
        """Test updating FileOperation execution status."""
        op = FileOperation(
            old_path="C:/file.pdf",
            new_path="C:/organized/file.pdf",
            category="Test",
        )
        op.executed = True
        op.error = "Some error"
        assert op.executed is True
        assert op.error == "Some error"

    def test_restoration_point_creation(self):
        """Test RestorationPoint dataclass creation."""
        ops = [
            FileOperation(
                old_path="C:/file1.pdf",
                new_path="C:/org/file1.pdf",
                category="Cat1",
            )
        ]
        point = RestorationPoint(
            timestamp="2025-11-13T14:30:00",
            root_dir="C:/source",
            target_dir="C:/target",
            file_operations=ops,
            metadata={"count": 1},
        )
        assert point.timestamp == "2025-11-13T14:30:00"
        assert len(point.file_operations) == 1
        assert point.metadata["count"] == 1


class TestJsonRestorationManager:
    """Test JsonRestorationManager core functionality."""

    def test_create_restoration_point(self, sample_classification_output, temp_dirs):
        """Test creating restoration point from classification output."""
        manager = JsonRestorationManager()
        point = manager.create_restoration_point(
            classification_output=sample_classification_output,
            target_dir=temp_dirs["target"],
            root_dir=temp_dirs["source"],
            timestamp="2025-11-13T14:30:00",
        )

        assert point.timestamp == "2025-11-13T14:30:00"
        assert point.root_dir == temp_dirs["source"]
        assert point.target_dir == temp_dirs["target"]
        assert len(point.file_operations) == 3

        # Verify path composition
        for op in point.file_operations:
            assert Path(op.old_path).is_absolute()
            assert Path(op.new_path).is_absolute()
            assert temp_dirs["target"] in op.new_path

    def test_save_and_load_restoration_point(self, sample_classification_output, temp_dirs):
        """Test saving and loading restoration point."""
        manager = JsonRestorationManager()
        manifest_path = Path(temp_dirs["manifest"]) / "test.json"

        # Create and save
        original = manager.create_restoration_point(
            classification_output=sample_classification_output,
            target_dir=temp_dirs["target"],
            root_dir=temp_dirs["source"],
        )
        manager.save_restoration_point(original, str(manifest_path))

        # Verify file exists and is valid JSON
        assert manifest_path.exists()
        with manifest_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert "timestamp" in data
        assert "file_operations" in data
        assert len(data["file_operations"]) == 3

        # Load and verify
        loaded = manager.load_restoration_point(str(manifest_path))
        assert loaded.timestamp == original.timestamp
        assert loaded.root_dir == original.root_dir
        assert loaded.target_dir == original.target_dir
        assert len(loaded.file_operations) == len(original.file_operations)

    def test_load_nonexistent_manifest(self):
        """Test loading non-existent manifest raises error."""
        manager = JsonRestorationManager()
        with pytest.raises(FileNotFoundError):
            manager.load_restoration_point("nonexistent.json")

    def test_load_corrupted_manifest(self, temp_dirs):
        """Test loading corrupted manifest raises error."""
        manager = JsonRestorationManager()
        manifest_path = Path(temp_dirs["manifest"]) / "corrupted.json"
        manifest_path.write_text("{invalid json", encoding="utf-8")

        with pytest.raises(ValueError, match="Corrupted manifest"):
            manager.load_restoration_point(str(manifest_path))

    def test_validate_restoration_point_success(self, sample_classification_output, temp_dirs):
        """Test validation passes for valid restoration point."""
        manager = JsonRestorationManager()
        point = manager.create_restoration_point(
            classification_output=sample_classification_output,
            target_dir=temp_dirs["target"],
            root_dir=temp_dirs["source"],
        )
        assert manager.validate_restoration_point(point) is True

    def test_validate_empty_operations(self):
        """Test validation fails for empty operations."""
        manager = JsonRestorationManager()
        point = RestorationPoint(
            timestamp="2025-11-13T14:30:00",
            root_dir="C:/source",
            target_dir="C:/target",
            file_operations=[],
        )
        assert manager.validate_restoration_point(point) is False

    def test_validate_duplicate_paths(self):
        """Test validation fails for duplicate old_paths."""
        manager = JsonRestorationManager()
        ops = [
            FileOperation(
                old_path="C:/file.pdf",
                new_path="C:/target/Cat1/file.pdf",
                category="Cat1",
            ),
            FileOperation(
                old_path="C:/file.pdf",  # Duplicate
                new_path="C:/target/Cat2/file.pdf",
                category="Cat2",
            ),
        ]
        point = RestorationPoint(
            timestamp="2025-11-13T14:30:00",
            root_dir="C:/source",
            target_dir="C:/target",
            file_operations=ops,
        )
        assert manager.validate_restoration_point(point) is False

    def test_compose_new_path(self):
        """Test path composition logic."""
        result = JsonRestorationManager._compose_new_path("C:/target", "Documents/file.pdf")
        assert Path(result).is_absolute()
        assert "Documents" in result
        assert "file.pdf" in result


class TestRestorationUseCase:
    """Test RestorationUseCase business logic."""

    def test_create_and_save_restoration_point(self, sample_classification_output, temp_dirs):
        """Test complete create and save workflow."""
        manager = JsonRestorationManager()
        use_case = RestorationUseCase(manager)
        manifest_path = Path(temp_dirs["manifest"]) / "test.json"

        point = use_case.create_and_save_restoration_point(
            classification_output=sample_classification_output,
            target_dir=temp_dirs["target"],
            root_dir=temp_dirs["source"],
            manifest_path=str(manifest_path),
        )

        assert point is not None
        assert manifest_path.exists()
        assert len(point.file_operations) == 3

    def test_get_restoration_point_info(self, sample_classification_output, temp_dirs):
        """Test getting restoration point information."""
        manager = JsonRestorationManager()
        use_case = RestorationUseCase(manager)
        manifest_path = Path(temp_dirs["manifest"]) / "info_test.json"

        use_case.create_and_save_restoration_point(
            classification_output=sample_classification_output,
            target_dir=temp_dirs["target"],
            root_dir=temp_dirs["source"],
            manifest_path=str(manifest_path),
        )

        info = use_case.get_restoration_point_info(str(manifest_path))
        assert info["total_operations"] == 3
        assert info["executed_operations"] == 0
        assert len(info["categories"]) > 0

    def test_validate_manifest(self, sample_classification_output, temp_dirs):
        """Test manifest validation."""
        manager = JsonRestorationManager()
        use_case = RestorationUseCase(manager)
        manifest_path = Path(temp_dirs["manifest"]) / "validate_test.json"

        use_case.create_and_save_restoration_point(
            classification_output=sample_classification_output,
            target_dir=temp_dirs["target"],
            root_dir=temp_dirs["source"],
            manifest_path=str(manifest_path),
        )

        assert use_case.validate_manifest(str(manifest_path)) is True
