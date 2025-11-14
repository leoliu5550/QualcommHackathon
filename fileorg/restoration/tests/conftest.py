"""Shared test fixtures for restoration module tests."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pytest


@dataclass
class MockFileMapping:
    """Mock FileMapping from Task3 for testing."""

    old_path: str
    new_relative_path: str
    category: str
    summary: str
    reason: str


@dataclass
class MockClassificationOutput:
    """Mock ClassificationOutput from Task3 for testing."""

    path_mappings: Dict[str, MockFileMapping]
    raw_response: str = "[STUB] Mock classification"
    metadata: Optional[Dict[str, Any]] = None


@pytest.fixture
def sample_classification_output(tmp_path):
    """Create sample classification output with real temp file paths."""
    # Create actual test files
    test_files = {}
    for name, ext in [("report", ".pdf"), ("memo", ".docx"), ("photo", ".jpg")]:
        file_path = tmp_path / "source" / f"{name}{ext}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(f"Content of {name}", encoding="utf-8")
        test_files[name] = str(file_path.resolve())

    mappings = {
        test_files["report"]: MockFileMapping(
            old_path=test_files["report"],
            new_relative_path="Documents/report.pdf",
            category="Documents",
            summary="Financial report",
            reason="PDF document",
        ),
        test_files["memo"]: MockFileMapping(
            old_path=test_files["memo"],
            new_relative_path="Office_Files/memo.docx",
            category="Office Files",
            summary="Office memo",
            reason="DOCX file",
        ),
        test_files["photo"]: MockFileMapping(
            old_path=test_files["photo"],
            new_relative_path="Images/photo.jpg",
            category="Images",
            summary="Photo",
            reason="Image file",
        ),
    }

    return MockClassificationOutput(
        path_mappings=mappings,
        metadata={"total_files": 3, "stub": True},
    )


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directory structure for testing."""
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "organized"
    manifest_dir = tmp_path / "manifests"

    source_dir.mkdir(exist_ok=True)
    target_dir.mkdir(exist_ok=True)
    manifest_dir.mkdir(exist_ok=True)

    return {
        "source": str(source_dir.resolve()),
        "target": str(target_dir.resolve()),
        "manifest": str(manifest_dir.resolve()),
        "tmp_path": tmp_path,
    }
