import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.file_parser import parser_manager

TEST_DATA_PATH = 'test/data/filetype'


@pytest.fixture(scope="module")
def test_files():
    files = os.listdir(TEST_DATA_PATH)
    return [os.path.join(TEST_DATA_PATH, f) for f in files]


def test_supported_formats():
    supported = parser_manager.get_supported_formats()
    print("Supported file formats:", supported)
    assert isinstance(supported, (list, set)) and len(supported) > 0


def test_single_file_parse(test_files):
    result = parser_manager.parse_file(test_files[0])
    print(result.to_dict())
    assert result.success is True
    assert result.content != ""


def test_multiple_files_parse(test_files):
    results = parser_manager.parse_multiple_files(test_files)
    for result in results:
        # print("#" * 30)
        # print(f"\nFile: {result.file_path}")
        # print(f"Status: {'Success' if result.success else 'Failure'}")
        # print(f"Content: {result.content[:100]}...")  # print first 100 chars
        assert result.success is True
        assert result.content != ""
