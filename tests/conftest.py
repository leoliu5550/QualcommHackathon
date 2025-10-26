from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(scope="session")
def test_data_path():
    return "tests/example_data"


@pytest.fixture(scope="function")
def unreadable_dir(tmp_path) -> Generator[Path, None, None]:
    """Create a temporary directory containing an unreadable file.

    This fixture creates a directory that is readable but contains a file
    with no read permissions. It is useful for testing the
    FileScanner._scan method's handling of OSError when accessing files.

    Args:
        tmp_path (Path): Built-in pytest fixture providing a temporary directory.

    Yields:
        Path: The path to the temporary directory with an unreadable file.

    Cleanup:
        Restores file permissions to allow pytest to delete the temporary directory.
    """
    # Create a readable directory
    bad_dir = tmp_path / "bad_dir"
    bad_dir.mkdir(0o755)

    # Create a file inside the directory and remove read permissions
    file_in_dir = bad_dir / "file.txt"
    file_in_dir.write_text("secret")
    file_in_dir.chmod(0o000)  # Remove all permissions

    yield bad_dir

    # Cleanup: restore file permissions so pytest can remove tmp_path
    file_in_dir.chmod(0o644)
