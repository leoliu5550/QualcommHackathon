"""
This test verifies that the file ID mapping system correctly handles
filenames with multiple consecutive spaces.
"""

import json

import pytest

from fileorg.llm_classifier.adapters.output_parsers import (
    PathMappingOutputParser,
    SummaryOutputParser,
)
from fileorg.llm_classifier.adapters.prompt_builders import (
    ClassificationPromptBuilder,
    SummaryPromptBuilder,
)
from fileorg.llm_classifier.adapters.sequential_file_id_mapper import SequentialFileIdMapper
from fileorg.llm_classifier.adapters.template_loader import Jinja2TemplateLoader
from fileorg.llm_classifier.application.file_classifier import FileClassifier
from fileorg.llm_classifier.ports.models import LLMInput


class MockLLMProviderForDoubleSpace:
    """
    Mock LLM provider that simulates the double-space normalization issue.

    This provider mimics the behavior where LLMs collapse multiple spaces
    into single spaces in their output.
    """

    def __init__(self):
        self.call_count = 0
        self.stage1_responses = []
        self.stage2_response = None
        self.stage1_file_ids = set()  # Track which file IDs we've seen in Stage 1

    def generate(self, messages, max_tokens=32768):
        """
        Generate mock responses.

        Stage 1: Returns file IDs (A001, A002, etc.) with keywords
        Stage 2: Returns file IDs with classification
        """
        self.call_count += 1

        # Extract the input from messages
        user_message = next((m for m in messages if m["role"] == "user"), None)
        if not user_message:
            return "{}"

        content = user_message["content"]

        # Parse JSON from content
        try:
            # Extract JSON from markdown if present
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                # Try to find JSON object in content
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]

            data = json.loads(json_str)

            # Check if this is Stage 1 or Stage 2
            # Strategy:
            # 1. If we've seen this file ID before → Stage 2
            # 2. If multiple keys → Stage 2 (classifying all files together)
            # 3. Otherwise → Stage 1 (first time seeing this single file)
            keys = list(data.keys())
            first_key = keys[0]

            if first_key in self.stage1_file_ids:
                # Already processed in Stage 1, must be Stage 2
                is_stage1 = False
            elif len(keys) > 1:
                # Multiple files = Stage 2 classification
                is_stage1 = False
            else:
                # Single file, not seen before = Stage 1
                is_stage1 = True

            if is_stage1:
                # Stage 1: Single file keyword extraction
                file_id = keys[0]

                # Map file IDs to keywords based on content
                content = data[file_id]

                if "Cluster" in content or "clustering" in content:
                    keyword = "Cluster Analysis"
                elif "Regression" in content or "regression" in content:
                    keyword = "Regression Techniques"
                elif "Recipe" in content or "cake" in content.lower():
                    keyword = "Chocolate Cake Recipe"
                elif "Budget" in content or "budget" in content.lower():
                    keyword = "Project Budget"
                elif "with  spaces" in file_id or "spaces" in content:
                    keyword = "Document"
                else:
                    keyword = "General Document"

                response = json.dumps({file_id: keyword}, ensure_ascii=False)
                self.stage1_responses.append(response)
                self.stage1_file_ids.add(file_id)  # Track that we've processed this file ID
                return response

            else:
                # Stage 2: Classification of all files
                # LLM returns file IDs with classification
                classifications = {}

                for file_id, keyword in data.items():
                    # Ensure keyword is a string
                    if not isinstance(keyword, str):
                        keyword = str(keyword)

                    if "Cluster" in keyword or "Regression" in keyword or "Machine Learning" in keyword:
                        classifications[file_id] = {
                            "category": "Machine Learning",
                            "summary": keyword,
                            "reason": "Educational content about ML algorithms",
                        }
                    elif "Recipe" in keyword or "Cake" in keyword or "Chocolate" in keyword:
                        classifications[file_id] = {"category": "Recipes", "summary": keyword, "reason": "Food recipe document"}
                    elif "Budget" in keyword or "Project" in keyword or "Financial" in keyword:
                        classifications[file_id] = {"category": "Financial Documents", "summary": keyword, "reason": "Budget and financial planning"}
                    elif "Document" in keyword:
                        classifications[file_id] = {"category": "General Documents", "summary": keyword, "reason": "General document"}
                    else:
                        classifications[file_id] = {"category": "General", "summary": keyword, "reason": "General document"}

                response = json.dumps(classifications, ensure_ascii=False)
                self.stage2_response = response
                return response

        except Exception as e:
            print(f"Mock LLM error: {e}")
            import traceback

            traceback.print_exc()
            return "{}"

    def get_device_info(self):
        return "MockProvider for Double-Space Test"


@pytest.fixture
def template_loader():
    """Create template loader."""
    return Jinja2TemplateLoader()


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    return MockLLMProviderForDoubleSpace()


@pytest.fixture
def file_id_mapper():
    """Create file ID mapper."""
    return SequentialFileIdMapper(prefix="A", id_width=3)


@pytest.fixture
def file_classifier(template_loader, mock_llm_provider, file_id_mapper):
    """Create FileClassifier with file ID mapping enabled."""
    summary_builder = SummaryPromptBuilder(template_loader=template_loader, provider="llama3b", version="v1")
    classification_builder = ClassificationPromptBuilder(template_loader=template_loader, provider="llama3b", version="v1")
    summary_parser = SummaryOutputParser()
    path_mapping_parser = PathMappingOutputParser()

    return FileClassifier(
        llm_provider=mock_llm_provider,
        summary_prompt_builder=summary_builder,
        summary_parser=summary_parser,
        classification_prompt_builder=classification_builder,
        classification_parser=path_mapping_parser,
        file_id_mapper=file_id_mapper,  # Enable file ID mapping
    )


def test_double_space_filename_handling(file_classifier, mock_llm_provider):
    """
    Test that files with double spaces in filenames are correctly handled.

    This is the main test for Issue #112.
    """
    # Input: Files with double spaces in filenames
    files = {
        "C:/Users/leo/Desktop/Ch7  Cluster analysis.txt": "Chapter about clustering algorithms",
        "C:/Users/leo/Desktop/Ch8  Regression techniques.txt": "Chapter about regression methods",
        "C:/Users/leo/Desktop/Recipe  Chocolate cake.txt": "Delicious chocolate cake recipe",
        "C:/Users/leo/Desktop/Project  Budget 2024.txt": "Annual project budget document",
    }

    input_text = json.dumps(files, ensure_ascii=False)
    llm_input = LLMInput(text=input_text, max_tokens=150000)

    # Execute classification
    result = file_classifier.classify(llm_input)

    # Verify all files were processed
    assert len(result.path_mappings) == 4, f"Expected 4 files, got {len(result.path_mappings)}"

    # Verify original paths are preserved (with double spaces)
    expected_paths = [
        "C:/Users/leo/Desktop/Ch7  Cluster analysis.txt",
        "C:/Users/leo/Desktop/Ch8  Regression techniques.txt",
        "C:/Users/leo/Desktop/Recipe  Chocolate cake.txt",
        "C:/Users/leo/Desktop/Project  Budget 2024.txt",
    ]

    for path in expected_paths:
        assert path in result.path_mappings, f"Path '{path}' not found in results"
        mapping = result.path_mappings[path]

        # Verify the mapping has correct structure
        assert mapping.old_path == path
        assert mapping.file_id is not None, f"File ID not set for {path}"
        assert mapping.new_relative_path is not None
        assert mapping.category is not None
        assert mapping.summary is not None
        assert mapping.reason is not None

        print(f"[OK] {path}")
        print(f"  File ID: {mapping.file_id}")
        print(f"  Category: {mapping.category}")
        print(f"  New path: {mapping.new_relative_path}")
        print()

    # Verify filenames are correctly extracted (not using IDs)
    ch7_mapping = result.path_mappings["C:/Users/leo/Desktop/Ch7  Cluster analysis.txt"]
    assert "Ch7  Cluster analysis.txt" in ch7_mapping.new_relative_path, f"Filename not preserved correctly: {ch7_mapping.new_relative_path}"

    # Verify Stage 1 and Stage 2 were called
    # Stage 1: 4 files = 4 calls
    # Stage 2: 1 call for classification
    assert mock_llm_provider.call_count == 5, f"Expected 5 LLM calls (4 Stage 1 + 1 Stage 2), got {mock_llm_provider.call_count}"

    print(f"[PASS] All tests passed! Mock LLM was called {mock_llm_provider.call_count} times.")


def test_file_id_mapping_with_stage1_responses(file_classifier, mock_llm_provider):
    """Verify that Stage 1 responses use file IDs instead of paths."""
    files = {
        "C:/test/file  with  spaces.txt": "Content with multiple spaces in filename",
    }

    input_text = json.dumps(files, ensure_ascii=False)
    llm_input = LLMInput(text=input_text, max_tokens=150000)

    # Execute classification
    file_classifier.classify(llm_input)

    # Check that Stage 1 response contains file ID (A001) not path
    stage1_response = mock_llm_provider.stage1_responses[0]
    assert "A001" in stage1_response, f"Expected file ID 'A001' in response: {stage1_response}"
    assert "file  with  spaces" not in stage1_response, f"Path should not be in Stage 1 response: {stage1_response}"

    print("[PASS] Stage 1 correctly uses file IDs")
    print(f"   Response: {stage1_response}")


def test_file_id_mapping_with_stage2_responses(file_classifier, mock_llm_provider):
    """Verify that Stage 2 responses use file IDs instead of paths."""
    files = {
        "C:/test1/file  one.txt": "First file",
        "C:/test2/file  two.txt": "Second file",
    }

    input_text = json.dumps(files, ensure_ascii=False)
    llm_input = LLMInput(text=input_text, max_tokens=150000)

    # Execute classification
    file_classifier.classify(llm_input)

    # Check that Stage 2 response contains file IDs not paths
    stage2_response = mock_llm_provider.stage2_response
    assert "A001" in stage2_response, f"Expected file ID 'A001' in Stage 2: {stage2_response}"
    assert "A002" in stage2_response, f"Expected file ID 'A002' in Stage 2: {stage2_response}"
    assert "file  one" not in stage2_response, f"Paths should not be in Stage 2 response: {stage2_response}"

    print("[PASS] Stage 2 correctly uses file IDs")
    print(f"   Response: {stage2_response}")


def test_backward_compatibility_without_file_id_mapper():
    """Test that system still works without file ID mapper (backward compatibility)."""

    class SimpleMockLLM:
        """Simple mock that returns paths directly (no file IDs)."""

        def __init__(self):
            self.call_count = 0

        def generate(self, messages, max_tokens=32768):
            self.call_count += 1

            # Parse input
            user_message = next((m for m in messages if m["role"] == "user"), None)
            if not user_message:
                return "{}"

            content = user_message["content"]

            # Extract JSON from markdown code blocks or plain text
            try:
                # Try to extract from markdown code block first
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                else:
                    # Find JSON object in content
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    if json_start == -1 or json_end == 0:
                        return "{}"
                    json_str = content[json_start:json_end]

                data = json.loads(json_str)

                keys = list(data.keys())
                first_value = str(data[keys[0]])

                # Check if Stage 1 or Stage 2 based on value length
                is_stage1 = len(first_value) > 20

                if is_stage1:
                    # Stage 1: Return path with keyword
                    path = keys[0]
                    return json.dumps({path: "General Document"}, ensure_ascii=False)
                else:
                    # Stage 2: Return classification
                    result = {}
                    for path in data.keys():
                        result[path] = {"category": "General", "summary": "General Document", "reason": "General file"}
                    return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                print(f"SimpleMockLLM error: {e}")
                import traceback

                traceback.print_exc()
                return "{}"

    template_loader = Jinja2TemplateLoader()
    mock_llm = SimpleMockLLM()

    # Create classifier WITHOUT file_id_mapper
    classifier = FileClassifier(
        llm_provider=mock_llm,
        summary_prompt_builder=SummaryPromptBuilder(template_loader, "llama3b", "v1"),
        summary_parser=SummaryOutputParser(),
        classification_prompt_builder=ClassificationPromptBuilder(template_loader, "llama3b", "v1"),
        classification_parser=PathMappingOutputParser(),
        file_id_mapper=None,  # No file ID mapper
    )

    # Note: This would fail with actual double-space files due to LLM normalization,
    # but with our mock it should work since mock doesn't normalize
    files = {
        "C:/test/normal_file.txt": "Normal filename content",
    }

    input_text = json.dumps(files, ensure_ascii=False)
    llm_input = LLMInput(text=input_text, max_tokens=150000)

    result = classifier.classify(llm_input)

    assert len(result.path_mappings) == 1
    # File ID should not be set when mapper is not used
    mapping = result.path_mappings["C:/test/normal_file.txt"]
    assert mapping.file_id is None, "File ID should be None in legacy mode"

    print("[PASS] Backward compatibility test passed (no file_id_mapper)")
