from pathlib import Path

import pytest

from fileorg.file_scan.scanner import FileScanner


@pytest.mark.scanner
def test_scanner_reads_all_files(test_data_path):
    scanner = FileScanner(test_data_path)
    expected_path = Path("./tests/example_data").resolve()

    assert scanner.root_dir == expected_path
    scanner_result = scanner.generate_report()
    assert len(scanner_result.get("files", None)) == scanner_result.get("file_count", None)
    assert scanner_result.get("files", None) is not None


@pytest.mark.scanner
def test_invalid_directory_path():
    invalid_path = Path("tests/non_existent_dir")
    with pytest.raises(FileNotFoundError) as exc_info:
        FileScanner(invalid_path)
    assert "does not exist" in str(exc_info.value)

    dir_but_file = Path("tests/test_scanner.py")
    with pytest.raises(NotADirectoryError) as exc_info:
        FileScanner(dir_but_file)
    assert "not a directory" in str(exc_info.value)
