"""End-to-end integration tests for restoration module."""

import shutil
from pathlib import Path

import pytest

from fileorg.restoration.adapters import JsonRestorationManager
from fileorg.restoration.application import RestorationUseCase
from fileorg.restoration.ports import FileOperation, RestorationPoint


class TestRestoreOperation:
    """Test file restoration (rollback) operations."""

    def test_restore_executed_operations(self, sample_classification_output, temp_dirs):
        """Test restoring files that were actually moved."""
        manager = JsonRestorationManager()
        use_case = RestorationUseCase(manager)
        manifest_path = Path(temp_dirs["manifest"]) / "restore_test.json"

        # Create restoration point
        point = use_case.create_and_save_restoration_point(
            classification_output=sample_classification_output,
            target_dir=temp_dirs["target"],
            root_dir=temp_dirs["source"],
            manifest_path=str(manifest_path),
        )

        # Simulate file organization: move one file
        first_op = point.file_operations[0]
        old_path = Path(first_op.old_path)
        new_path = Path(first_op.new_path)

        # Move file
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path), str(new_path))

        # Update manifest with execution status
        point.file_operations[0].executed = True
        manager.save_restoration_point(point, str(manifest_path))

        # Verify file moved
        assert not old_path.exists()
        assert new_path.exists()

        # Execute restore
        result = use_case.restore_files(str(manifest_path))

        # Verify restoration
        assert result["total"] == 3
        assert result["restored"] == 1
        assert result["skipped"] == 2  # Not executed

        # Verify file restored
        assert old_path.exists()
        assert not new_path.exists()

    def test_restore_skips_non_executed(self, temp_dirs):
        """Test that non-executed operations are skipped."""
        manager = JsonRestorationManager()
        use_case = RestorationUseCase(manager)
        manifest_path = Path(temp_dirs["manifest"]) / "skip_test.json"

        ops = [
            FileOperation(
                old_path="C:/source/file.pdf",
                new_path="C:/target/file.pdf",
                category="Test",
                executed=False,  # Not executed
            )
        ]
        point = RestorationPoint(
            timestamp="2025-11-13T14:30:00",
            root_dir=temp_dirs["source"],
            target_dir=temp_dirs["target"],
            file_operations=ops,
        )
        manager.save_restoration_point(point, str(manifest_path))

        result = use_case.restore_files(str(manifest_path))
        assert result["skipped"] == 1
        assert result["restored"] == 0

    def test_restore_handles_missing_files(self, temp_dirs):
        """Test restore handles missing files gracefully."""
        manager = JsonRestorationManager()
        use_case = RestorationUseCase(manager)
        manifest_path = Path(temp_dirs["manifest"]) / "missing_test.json"

        ops = [
            FileOperation(
                old_path="C:/source/file.pdf",
                new_path="C:/target/nonexistent.pdf",  # Doesn't exist
                category="Test",
                executed=True,
            )
        ]
        point = RestorationPoint(
            timestamp="2025-11-13T14:30:00",
            root_dir=temp_dirs["source"],
            target_dir=temp_dirs["target"],
            file_operations=ops,
        )
        manager.save_restoration_point(point, str(manifest_path))

        result = use_case.restore_files(str(manifest_path))
        assert result["failed"] == 1
        assert len(result["errors"]) == 1


class TestFullPipeline:
    """Test complete pipeline simulation."""

    def test_full_organization_and_restore_cycle(self, sample_classification_output, temp_dirs):
        """Test complete cycle: create → organize → restore."""
        manager = JsonRestorationManager()
        use_case = RestorationUseCase(manager)
        manifest_path = Path(temp_dirs["manifest"]) / "full_cycle.json"

        # Step 1: Create restoration point
        point = use_case.create_and_save_restoration_point(
            classification_output=sample_classification_output,
            target_dir=temp_dirs["target"],
            root_dir=temp_dirs["source"],
            manifest_path=str(manifest_path),
        )

        # Store original file paths for verification
        original_files = [Path(op.old_path) for op in point.file_operations]
        assert all(f.exists() for f in original_files)

        # Step 2: Simulate file organization (move all files)
        for operation in point.file_operations:
            old_path = Path(operation.old_path)
            new_path = Path(operation.new_path)

            if old_path.exists():
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_path), str(new_path))
                operation.executed = True

        # Save updated manifest
        manager.save_restoration_point(point, str(manifest_path))

        # Verify files are organized
        assert all(not f.exists() for f in original_files)
        assert all(Path(op.new_path).exists() for op in point.file_operations if op.executed)

        # Step 3: Restore files
        result = use_case.restore_files(str(manifest_path))

        # Verify restoration success
        assert result["restored"] == 3
        assert result["failed"] == 0

        # Verify files are back at original locations
        assert all(f.exists() for f in original_files)

    def test_partial_execution_restoration(self, sample_classification_output, temp_dirs):
        """Test restoration when only some operations were executed."""
        manager = JsonRestorationManager()
        use_case = RestorationUseCase(manager)
        manifest_path = Path(temp_dirs["manifest"]) / "partial.json"

        # Create restoration point
        point = use_case.create_and_save_restoration_point(
            classification_output=sample_classification_output,
            target_dir=temp_dirs["target"],
            root_dir=temp_dirs["source"],
            manifest_path=str(manifest_path),
        )

        # Execute only first operation
        first_op = point.file_operations[0]
        old_path = Path(first_op.old_path)
        new_path = Path(first_op.new_path)

        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path), str(new_path))
        first_op.executed = True

        # Save partial execution
        manager.save_restoration_point(point, str(manifest_path))

        # Restore
        result = use_case.restore_files(str(manifest_path))

        # Should restore 1, skip 2
        assert result["restored"] == 1
        assert result["skipped"] == 2


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_restore_nonexistent_manifest(self):
        """Test restoring from non-existent manifest."""
        manager = JsonRestorationManager()
        use_case = RestorationUseCase(manager)

        with pytest.raises(FileNotFoundError):
            use_case.restore_files("nonexistent.json")

    def test_create_with_invalid_classification_output(self, temp_dirs):
        """Test creating restoration point with invalid input."""
        manager = JsonRestorationManager()

        class InvalidOutput:
            pass

        with pytest.raises(ValueError, match="path_mappings"):
            manager.create_restoration_point(
                classification_output=InvalidOutput(),
                target_dir=temp_dirs["target"],
                root_dir=temp_dirs["source"],
            )

    def test_save_creates_parent_directories(self, temp_dirs):
        """Test that save creates parent directories."""
        manager = JsonRestorationManager()
        nested_path = Path(temp_dirs["manifest"]) / "deep" / "nested" / "manifest.json"

        point = RestorationPoint(
            timestamp="2025-11-13T14:30:00",
            root_dir=temp_dirs["source"],
            target_dir=temp_dirs["target"],
            file_operations=[
                FileOperation(
                    old_path="C:/file.pdf",
                    new_path="C:/target/file.pdf",
                    category="Test",
                )
            ],
        )

        manager.save_restoration_point(point, str(nested_path))
        assert nested_path.exists()
