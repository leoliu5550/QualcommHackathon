"""
E2E tests for two-stage classification with real components.

These tests use real adapters (prompt builders, parsers) but with
lightweight LLM mocking to ensure CI/CD compatibility.

Goals:
- Verify complete flow: prompts → LLM → parsing → output
- Fast execution (< 30s)
- CI/CD friendly (no GPU required)
- Validate real template loading and parsing logic
"""

import json
import os

import pytest

from fileorg.llm_classifier.adapters.output_parsers import (
    PathMappingOutputParser,
    SummaryOutputParser,
)
from fileorg.llm_classifier.adapters.prompt_builders import (
    ClassificationPromptBuilder,
    SummaryPromptBuilder,
)
from fileorg.llm_classifier.adapters.template_loader import Jinja2TemplateLoader
from fileorg.llm_classifier.application.file_classifier import FileClassifier
from fileorg.llm_classifier.ports.models import LLMInput


class SimpleLLMProvider:
    """
    Lightweight LLM mock that simulates real LLM behavior.

    This is NOT a pure mock - it validates prompt structure and
    returns realistic JSON responses.
    """

    def __init__(self):
        self.call_count = 0
        self.prompts_received = []

    def generate(self, messages, max_tokens=32768):
        """Generate realistic responses based on prompt analysis."""
        self.call_count += 1

        # Validate message structure (like real LLM)
        assert isinstance(messages, list), "Messages must be a list"
        assert len(messages) > 0, "Messages cannot be empty"
        assert all(isinstance(m, dict) for m in messages), "Each message must be a dict"

        # Store prompt for inspection
        self.prompts_received.append(messages)

        # Extract file paths from the last message
        last_message = messages[-1]["content"]

        # Import regex
        import json
        import re

        # Extract the user message section (this contains the actual files, not template examples)
        # Look for content between <|start_header_id|>user<|end_header_id|> and <|eot_id|>
        user_section_match = re.search(r"<\|start_header_id\|>user<\|end_header_id\|>(.*?)<\|eot_id\|>", last_message, re.DOTALL)

        user_content = None
        if user_section_match:
            user_content = user_section_match.group(1)
            # Extract file paths from user content only
            actual_paths = re.findall(r'"([^"]+\.(?:pdf|txt|docx|xlsx))"', user_content)
        else:
            # Fallback: extract all paths and try to filter
            all_paths = re.findall(r'"([^"]+\.(?:pdf|txt|docx|xlsx))"', last_message)
            actual_paths = [p for p in all_paths if "/absolute/path/" not in p and "Documents/report" not in p]

        # If no paths found in filtered results, try extracting from JSON structures directly
        if not actual_paths:
            # Try to parse as JSON to extract keys (common in Stage 2)
            try:
                # Look for JSON objects in the message
                json_pattern = r'\{[^{}]*"([^"]+\.(?:pdf|txt|docx|xlsx))"[^{}]*:[^{}]*\}'
                json_matches = re.findall(json_pattern, last_message)
                if json_matches:
                    actual_paths = [p for p in json_matches if "/absolute/path/" not in p and "Documents/report" not in p]
            except Exception:
                pass

        # Determine stage by checking for specific indicators
        # Stage 2: Classification - multiple files OR specific classify instruction
        # Check for the specific instruction phrase used in Stage 2
        is_stage2 = (
            ("classify these files" in last_message.lower())  # Specific Stage 2 instruction
            or ("財務" in last_message and "會議" in last_message)  # Multiple different keywords suggest Stage 2
            or ("財務" in last_message and "中文文件" in last_message)
            or ("會議" in last_message and "中文文件" in last_message)
            or (len(actual_paths) > 1 and ("categor" in last_message.lower() or "classify" in last_message.lower()))
        )

        # Stage 1: Keyword extraction - looks for "extract" instruction OR single file with keyword instruction
        is_stage1 = (
            ("extract" in last_message.lower() and not is_stage2)
            or (len(actual_paths) == 1 and "please extract" in last_message.lower())
            or (len(actual_paths) == 1 and not is_stage2)
        )

        # Stage 2: Classification (check first as it has priority)
        if is_stage2:
            # Initialize result dict for Stage 2
            result = {}

            # Parse keywords from the user section (where the actual data is)
            search_content = user_content if user_section_match else last_message

            # Try to extract JSON from code blocks (```json ... ```)
            json_block_match = re.search(r"```json\s*(.*?)\s*```", search_content, re.DOTALL)
            if json_block_match:
                json_str = json_block_match.group(1).strip()
            else:
                json_str = search_content.strip()

            # Try to parse as JSON first (Stage 2 input is usually JSON)
            keyword_dict = None
            try:
                keyword_dict = json.loads(json_str)
            except json.JSONDecodeError:
                # Try to find JSON object in the content
                json_obj_match = re.search(r'\{[^{}]*"[^"]+\.[^"]+"\s*:[^{}]*\}', search_content, re.DOTALL)
                if json_obj_match:
                    try:
                        keyword_dict = json.loads(json_obj_match.group(0))
                    except json.JSONDecodeError:
                        pass

            if keyword_dict and isinstance(keyword_dict, dict):
                for path, keyword in keyword_dict.items():
                    # Skip template paths
                    if "/absolute/path/" in path or "Documents/report" in path:
                        continue

                    # Classify based on keyword
                    if keyword == "財務":
                        result[path] = {"category": "Financial Reports", "summary": "財務", "reason": "Financial document based on keyword"}
                    elif keyword == "會議":
                        result[path] = {"category": "Meeting Notes", "summary": "會議", "reason": "Meeting documentation based on keyword"}
                    elif keyword == "中文文件":
                        result[path] = {"category": "Chinese Documents", "summary": "中文文件", "reason": "Chinese document based on keyword"}
                    elif keyword == "日本語":
                        result[path] = {"category": "Japanese Documents", "summary": "日本語", "reason": "Japanese document based on keyword"}
                    else:
                        result[path] = {"category": "General Documents", "summary": keyword, "reason": "Generic document"}

            # If JSON parsing failed, try line-by-line parsing
            if not result:
                # Fallback to line-by-line parsing
                for line in search_content.split("\n"):
                    if '"' not in line:
                        continue

                    # Extract path and keyword from each line
                    path_keyword_match = re.search(r'"([^"]+\.(?:pdf|txt|docx|xlsx))":\s*"([^"]*)"', line)
                    if not path_keyword_match:
                        continue

                    path = path_keyword_match.group(1)
                    keyword = path_keyword_match.group(2)

                    # Skip template paths
                    if "/absolute/path/" in path or "Documents/report" in path:
                        continue

                    # Classify based on keyword
                    if keyword == "財務":
                        result[path] = {"category": "Financial Reports", "summary": "財務", "reason": "Financial document based on keyword"}
                    elif keyword == "會議":
                        result[path] = {"category": "Meeting Notes", "summary": "會議", "reason": "Meeting documentation based on keyword"}
                    elif keyword == "中文文件":
                        result[path] = {"category": "Chinese Documents", "summary": "中文文件", "reason": "Chinese document based on keyword"}
                    elif keyword == "日本語":
                        result[path] = {"category": "Japanese Documents", "summary": "日本語", "reason": "Japanese document based on keyword"}
                    else:
                        result[path] = {"category": "General Documents", "summary": keyword, "reason": "Generic document"}

            # If result is still empty, use actual_paths as fallback
            if not result and actual_paths:
                for path in actual_paths:
                    result[path] = {"category": "General Documents", "summary": "文件", "reason": "Generic document"}

            if result:
                return json.dumps(result, ensure_ascii=False)

        # Stage 1: Keyword extraction
        elif is_stage1 or (actual_paths and len(actual_paths) == 1 and not is_stage2):
            # Process the first actual file path
            file_path = actual_paths[0]

            # First try to extract content from the actual file data in the prompt
            content_match = re.search(rf'"{re.escape(file_path)}":\s*"([^"]*)"', last_message)

            if content_match:
                # Extract keyword based on actual file content
                content = content_match.group(1).lower()
                if "financial" in content or "revenue" in content:
                    keyword = "財務"
                elif "meeting" in content or "sync" in content or "notes" in content:
                    keyword = "會議"
                elif "test" in content and "test1" in file_path.lower():
                    # Special case for test fixtures
                    keyword = "財務"
                elif "test" in content and "test2" in file_path.lower():
                    # Special case for test fixtures
                    keyword = "會議"
                else:
                    keyword = "文件"
            elif "financial" in file_path.lower() or "report" in file_path.lower():
                keyword = "財務"
            elif "meeting" in file_path.lower() or "notes" in file_path.lower():
                keyword = "會議"
            elif "中文" in file_path:
                keyword = "中文文件"
            elif "日本語" in file_path:
                keyword = "日本語"
            elif "single" in file_path.lower():
                keyword = "文件"
            else:
                keyword = "文件"

            return json.dumps({file_path: keyword}, ensure_ascii=False)

        # Fallback: return generic response for any remaining cases
        if actual_paths:
            # Check if it looks like Stage 1 (single file with extract instruction)
            if len(actual_paths) == 1 and "extract" in last_message.lower():
                # Stage 1 fallback
                return json.dumps({actual_paths[0]: "文件"}, ensure_ascii=False)
            else:
                # Stage 2 fallback (multiple files or classify instruction)
                result = {}
                for path in actual_paths:
                    result[path] = {"category": "General Documents", "summary": "文件", "reason": "Generic document"}
                return json.dumps(result, ensure_ascii=False)

        return json.dumps({"error": "Unexpected prompt structure"}, ensure_ascii=False)

    def get_device_info(self):
        return {"device": "mock", "provider": "SimpleLLMProvider"}


@pytest.fixture
def template_loader():
    """Real template loader."""
    return Jinja2TemplateLoader()


@pytest.fixture
def llm_provider():
    """Lightweight LLM mock."""
    return SimpleLLMProvider()


@pytest.fixture
def classifier(template_loader, llm_provider):
    """FileClassifier with real adapters + mock LLM."""
    summary_prompt_builder = SummaryPromptBuilder(
        template_loader=template_loader,
        provider="llama3b",
        version="v1",
    )

    classification_prompt_builder = ClassificationPromptBuilder(
        template_loader=template_loader,
        provider="llama3b",
        version="v1",
    )

    summary_parser = SummaryOutputParser()
    classification_parser = PathMappingOutputParser()

    return FileClassifier(
        llm_provider=llm_provider,
        summary_prompt_builder=summary_prompt_builder,
        summary_parser=summary_parser,
        classification_prompt_builder=classification_prompt_builder,
        classification_parser=classification_parser,
    )


class TestTwoStageE2E:
    """E2E tests with real components."""

    def test_complete_two_stage_flow(self, classifier, llm_provider):
        """Test complete flow from input to output."""
        files = {
            "C:/test1.pdf": "Annual financial report with revenue data",
            "C:/test2.txt": "Meeting notes from team sync",
        }

        input_data = LLMInput(text=json.dumps(files))
        result = classifier.classify(input_data)

        # Verify LLM was called 3 times (2 Stage 1 + 1 Stage 2)
        assert llm_provider.call_count == 3

        # Verify prompts were properly formatted
        assert len(llm_provider.prompts_received) == 3
        for prompt in llm_provider.prompts_received:
            assert isinstance(prompt, list)
            assert len(prompt) > 0
            # Verify Llama format tokens exist
            assert any("<|begin_of_text|>" in str(m.get("content", "")) for m in prompt)

        # Verify output structure
        assert len(result.path_mappings) == 2
        assert "C:/test1.pdf" in result.path_mappings
        assert "C:/test2.txt" in result.path_mappings

        # Verify Stage 1 keywords preserved in Stage 2
        assert result.path_mappings["C:/test1.pdf"].summary == "財務"
        assert result.path_mappings["C:/test2.txt"].summary == "會議"

        # Verify proper categorization
        assert result.path_mappings["C:/test1.pdf"].category == "Financial Reports"
        assert result.path_mappings["C:/test2.txt"].category == "Meeting Notes"

        # Verify path assembly
        assert "Financial_Reports/" in result.path_mappings["C:/test1.pdf"].new_relative_path
        assert "Meeting_Notes/" in result.path_mappings["C:/test2.txt"].new_relative_path

        # Verify metadata
        assert result.metadata["file_count"] == 2
        assert "stage1_time_ms" in result.metadata
        assert "stage2_time_ms" in result.metadata
        assert "total_time_ms" in result.metadata

        # Verify raw responses from both stages
        assert "stage1_summaries" in result.raw_responses
        assert "stage2_classification" in result.raw_responses

    def test_stage1_prompt_structure(self, classifier, llm_provider):
        """Verify Stage 1 prompts are correctly structured."""
        files = {"C:/test1.pdf": "Test content"}
        input_data = LLMInput(text=json.dumps(files))

        summaries, _ = classifier.generate_summaries(input_data)

        # Check prompt was called
        assert llm_provider.call_count == 1
        prompt = llm_provider.prompts_received[0]

        # Verify prompt structure
        content = prompt[-1]["content"]
        assert "<|begin_of_text|>" in content
        assert "<|start_header_id|>system<|end_header_id|>" in content
        assert "<|start_header_id|>user<|end_header_id|>" in content
        assert "<|start_header_id|>assistant<|end_header_id|>" in content

        # Verify Stage 1 specific instructions
        assert "keyword" in content.lower() or "extract" in content.lower()

    def test_stage2_prompt_structure(self, classifier, llm_provider):
        """Verify Stage 2 prompts are correctly structured."""
        # First generate summaries
        files = {"C:/test1.pdf": "Test", "C:/test2.txt": "Test"}
        input_data = LLMInput(text=json.dumps(files))
        summaries, _ = classifier.generate_summaries(input_data)

        # Reset counter to focus on Stage 2
        stage1_count = llm_provider.call_count

        # Then classify
        path_mappings, _ = classifier.classify_by_summaries(summaries)

        # Check Stage 2 prompt
        assert llm_provider.call_count == stage1_count + 1
        stage2_prompt = llm_provider.prompts_received[-1]

        content = stage2_prompt[-1]["content"]

        # Verify Llama format
        assert "<|begin_of_text|>" in content
        assert "<|start_header_id|>system<|end_header_id|>" in content

        # Verify Stage 2 specific instructions
        assert "classif" in content.lower() or "categor" in content.lower()

        # Verify keywords are present (not original content)
        assert "財務" in content
        assert "會議" in content

    def test_template_loading_v1(self, template_loader):
        """Verify v1 templates exist and load correctly."""
        # Stage 1 templates
        assert template_loader.template_exists("llama3b", "v1", "summary_system")
        assert template_loader.template_exists("llama3b", "v1", "summary_user")

        # Stage 2 templates
        assert template_loader.template_exists("llama3b", "v1", "classification_system")
        assert template_loader.template_exists("llama3b", "v1", "classification_user")

        # Load and render
        summary_sys = template_loader.load_template("llama3b", "v1", "summary_system")
        rendered = summary_sys.render()
        assert rendered.strip() != ""
        assert "keyword" in rendered.lower()

    def test_parsing_edge_cases(self, classifier):
        """Test parsing handles edge cases correctly."""
        # Test single file
        single_file = LLMInput(text=json.dumps({"C:/single.pdf": "content"}))
        result = classifier.classify(single_file)
        assert len(result.path_mappings) == 1

        # Test Unicode content
        unicode_files = {"C:/中文.txt": "這是中文內容", "C:/日本語.txt": "これは日本語です"}
        unicode_input = LLMInput(text=json.dumps(unicode_files, ensure_ascii=False))
        result = classifier.classify(unicode_input)
        assert len(result.path_mappings) == 2

    def test_error_handling(self, classifier, llm_provider):
        """Test error handling in E2E flow."""
        # Empty input
        with pytest.raises(ValueError, match="Input text cannot be empty"):
            classifier.classify(LLMInput(text=""))

        # Invalid JSON
        with pytest.raises(ValueError):
            classifier.classify(LLMInput(text="not json"))


@pytest.mark.skipif(os.getenv("SKIP_E2E_TESTS") == "1", reason="E2E tests skipped (SKIP_E2E_TESTS=1)")
class TestE2EPerformance:
    """E2E performance checks (optional)."""

    def test_performance_baseline(self, classifier):
        """Verify E2E execution time is reasonable."""
        import time

        files = {
            "C:/test1.pdf": "Test content " * 100,
            "C:/test2.txt": "Test content " * 100,
        }

        input_data = LLMInput(text=json.dumps(files))

        start = time.time()
        result = classifier.classify(input_data)
        elapsed = time.time() - start

        # Should complete in reasonable time (with mock LLM)
        assert elapsed < 5.0, f"E2E took too long: {elapsed:.2f}s"

        # Verify metadata timing
        assert result.metadata["total_time_ms"] < 5000
