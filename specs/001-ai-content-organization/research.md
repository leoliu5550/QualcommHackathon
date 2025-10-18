# Research & Design Decisions: AI-Powered File Organization

**Feature**: 001-ai-content-organization
**Date**: 2025-10-18
**Status**: Complete

## Overview

This document captures the research findings and design decisions for implementing FileOrg's AI-powered file organization system. All technical context was clearly defined from the start, so this research focuses on best practices, integration patterns, and implementation strategies.

---

## 1. AI/LLM Integration Strategy

### Decision: Hugging Face Transformers with Qualcomm SDK Backend

**Rationale**:
- **Hugging Face Transformers** provides robust, production-ready LLM inference capabilities
- **Qualcomm SDK** enables hardware acceleration on NPU-equipped devices (Snapdragon laptops/devices)
- Dual-backend support (NPU + CPU/GPU) ensures broad device compatibility
- Local inference preserves user privacy (no cloud API calls)

**Implementation Approach**:
```
fileorg/ai/config.py controls backend selection:
- "qualcomm" backend → httpx client to NPU API endpoint
- "local" backend → Hugging Face transformers with torch/CPU
```

**Alternatives Considered**:
1. **Cloud-based LLM APIs (OpenAI, Anthropic)**: Rejected due to privacy concerns - users don't want documents sent to external servers
2. **ONNX Runtime with quantized models**: Considered but Hugging Face provides better model ecosystem and Qualcomm SDK handles optimization
3. **Local-only (no NPU support)**: Rejected because hackathon requirement is Qualcomm SDK integration

**Best Practices**:
- Use model caching in `fileorg/ai/model/` to avoid repeated downloads
- Implement timeout handling for NPU API calls (network reliability)
- Fallback mechanism: if NPU unavailable, gracefully degrade to CPU/GPU
- Batch inference where possible to improve throughput

---

## 2. Content Extraction from Multiple File Formats

### Decision: Format-Specific Parser Libraries with Factory Pattern

**Rationale**:
- Each file format requires specialized parsing (PDF structure differs from DOCX)
- Factory pattern (`parsers/factory.py`) enables clean selection logic
- Industry-standard libraries proven in production environments

**Parser Library Choices**:

| Format | Library | Justification |
|--------|---------|---------------|
| PDF | pypdf | Lightweight, pure Python, handles text extraction well |
| Word (.docx) | python-docx | Official OpenXML parser, robust for modern Word files |
| Excel (.xlsx) | openpyxl | Standard for Excel file manipulation, supports formulas |
| PowerPoint (.pptx) | python-pptx | Official OpenXML parser for presentations |
| Plain Text | Built-in `open()` | No library needed for .txt files |
| HTML | Built-in or html.parser | Standard library sufficient for content extraction |
| JSON | Built-in `json` | Standard library handles JSON parsing |
| XML | Built-in `xml.etree.ElementTree` | Standard library XML parser |
| CSV | Built-in `csv` | Standard library CSV reader |
| Markdown | Built-in (read as text) | Markdown is plain text with formatting |

**Alternatives Considered**:
1. **Apache Tika (Java-based)**: Rejected due to Java dependency overhead and cross-platform complexity
2. **Textract (AWS service)**: Rejected due to cloud dependency violating privacy requirement
3. **Universal document parser (single library)**: No single library handles all formats well

**Best Practices**:
- Extract content summaries, not full text (reduce memory for large documents)
- Handle exceptions gracefully - corrupted files should not crash the system
- Implement parser interface contract to ensure consistency
- Log parsing errors with file path for user review

**Edge Case Handling**:
- Password-protected files → log error, categorize as "Unprocessable_Files"
- Corrupted files → log error, continue processing remaining files
- Empty files → minimal content, categorize based on extension/name
- Very large files (>100MB) → stream content or extract first N pages

---

## 3. File Organization Workflow Architecture

### Decision: Pipeline Architecture with Phase Separation

**Rationale**:
- Clear separation of concerns enables testing and debugging
- Each phase can be independently verified
- Pipeline flow matches user mental model (scan → analyze → organize)

**Pipeline Phases**:

```
Phase 1: File Discovery (fileorg/scanner/)
├─ Recursive directory traversal
├─ Filter system directories (.git, __pycache__, etc.)
├─ Collect file metadata (path, size, dates)
└─ Output: List[FileMetadata]

Phase 2: Content Extraction (fileorg/parsers/)
├─ Select appropriate parser per file type
├─ Extract text content or summaries
├─ Handle parsing errors gracefully
└─ Output: List[FileWithContent]

Phase 3: AI Classification (fileorg/ai/classifier.py)
├─ Batch files for efficient inference
├─ Generate category names using LLM
├─ Group files by semantic similarity
└─ Output: Dict[CategoryName, List[File]]

Phase 4: File Organization (fileorg/core/organizer.py)
├─ Create backup data structure
├─ Create category folders
├─ Move files to organized locations
└─ Output: OrganizationResult

Phase 5: Report Generation (fileorg/reporter/)
├─ Generate HTML tree visualization
├─ Create Markdown summary
├─ Calculate statistics
└─ Output: Reports in designated folder
```

**Preview Mode Variation**:
- Execute Phases 1-3 fully
- Phase 4: Generate backup data BUT do NOT move files
- Phase 5: Generate reports showing *proposed* structure
- User can review reports before executing actual organization

**Restore Mode**:
- Read backup JSON (`{original_path: new_path}`)
- Reverse all file movements
- Validate all files restored correctly

**Alternatives Considered**:
1. **Event-driven architecture**: Rejected as over-engineered for single-user CLI tool
2. **Database-backed workflow**: Rejected - file system operations sufficient, no persistence needed beyond backup JSON
3. **Async/parallel processing**: Deferred to optimization phase - sequential pipeline is simpler and sufficient for MVP

**Best Practices**:
- Atomic operations where possible (move + update backup atomically)
- Transaction log for partial completion recovery
- Progress callbacks for user feedback (especially GUI)
- Rollback on critical errors

---

## 4. Backup and Restoration Mechanism

### Decision: JSON-based Backup with Path Mapping

**Rationale**:
- Simple, human-readable format (JSON)
- No database overhead
- Easy to inspect and debug
- Sufficient for tracking thousands of file movements

**Backup Data Structure**:
```json
{
  "version": "1.0",
  "timestamp": "2025-10-18T14:30:00Z",
  "source_folder": "/Users/name/Downloads",
  "file_mappings": [
    {
      "original_path": "/Users/name/Downloads/invoice.pdf",
      "new_path": "/Users/name/Downloads/Financial_Documents/invoice.pdf",
      "timestamp": "2025-10-18T14:30:05Z"
    }
  ]
}
```

**Storage Location**: `.backup/file_paths.json` in the organized folder root

**Alternatives Considered**:
1. **SQLite database**: Rejected as over-engineered for simple key-value mapping
2. **CSV file**: Rejected due to escaping complexity for file paths with special characters
3. **No backup**: Rejected - violates safety-first principle

**Best Practices**:
- Write backup file BEFORE moving any files
- Update backup atomically after each file move (append-only log style)
- Validate backup integrity before restore (check all files exist)
- Store backup version for future format evolution

---

## 5. AI Prompt Engineering for File Categorization

### Decision: Few-Shot Learning with Domain Detection

**Rationale**:
- Few-shot examples guide LLM to generate appropriate category names
- Domain detection enables context-aware categorization (work vs. personal)
- Prompt optimization reduces token usage and improves accuracy

**Prompt Structure** (from existing `fileorg/ai/prompt_engine/`):

```
System: You are a file organization assistant. Generate concise, human-readable
category folder names based on document content.

Examples:
- Invoice content → "Financial_Documents"
- Medical report → "Medical_Records"
- Meeting notes → "Work_Notes"

Rules:
- Use underscores, no spaces
- 1-3 words maximum
- Semantic meaning over file types
- Avoid overly specific names

Content: [extracted document text]
Category:
```

**Configuration Presets** (from `fileorg/ai/config.py`):
- **Legacy**: Simple prompt, basic categorization
- **Balanced**: Few-shot examples, moderate token usage
- **Advanced**: Domain detection + few-shot, highest accuracy

**Alternatives Considered**:
1. **Zero-shot prompting**: Rejected - less consistent category naming
2. **Fine-tuned model**: Rejected - requires training data and infrastructure
3. **Rule-based classification**: Rejected - cannot understand semantic meaning

**Best Practices**:
- Limit token usage (extract summaries, not full documents)
- Cache category mappings to reduce redundant API calls
- Temperature = 0.3-0.5 for consistent but not overly rigid categories
- Validate generated names (sanitize special characters)

---

## 6. Performance Optimization Strategies

### Decision: Batch Processing with Memory Management

**Rationale**:
- Meet performance requirements: 100+ files/minute
- Stay within memory constraints: <2GB for 2000 files
- Balance throughput with resource usage

**Optimization Techniques**:

1. **Batch AI Inference**:
   - Group files into batches of 10-20
   - Single LLM call with multiple content samples
   - Reduces API overhead and improves throughput

2. **Content Summary Extraction**:
   - Extract first N pages/paragraphs instead of full content
   - Target: 500-1000 tokens per document for AI analysis
   - Reduces memory footprint and LLM processing time

3. **Lazy Loading**:
   - Parse file content on-demand during AI phase
   - Don't hold all file contents in memory simultaneously
   - Process in streaming batches

4. **Concurrent File Operations**:
   - Use `concurrent.futures` for I/O-bound operations (file reading)
   - Keep AI inference sequential (or batch) to avoid resource contention
   - Parallel report generation (HTML + Markdown + stats)

5. **Progress Tracking**:
   - Emit progress events every 10 files processed
   - GUI updates without blocking main thread
   - CLI progress bar with percentage

**Benchmarking Strategy**:
```python
# tests/benchmark/test_performance.py
def test_organize_100_files_under_5_minutes():
    """Verify processing meets speed requirement."""
    start = time.time()
    organize_folder(test_folder_with_100_files)
    duration = time.time() - start
    assert duration < 300  # 5 minutes
```

**Alternatives Considered**:
1. **Full parallel processing**: Rejected - complex coordination, resource contention
2. **Database caching**: Rejected - file system I/O sufficient
3. **Asynchronous architecture**: Deferred - adds complexity, not needed for MVP

---

## 7. Testing Strategy

### Decision: Test Pyramid with Contract-First Approach

**Rationale**:
- Contract tests ensure interfaces remain stable
- Integration tests verify end-to-end workflows
- Unit tests for complex logic only (avoid testing implementation details)

**Test Hierarchy** (per Constitution):

**1. Contract Tests** (highest priority):
```python
# tests/contract/test_cli_interface.py
def test_cli_accepts_folder_path():
    """CLI must accept folder path as first argument."""
    result = run_cli(["fileorg", "/path/to/folder"])
    assert result.exit_code == 0

def test_preview_flag_prevents_file_movement():
    """--preview flag must not move files."""
    run_cli(["fileorg", test_folder, "--preview"])
    assert all_files_in_original_locations()

# tests/contract/test_parser_contracts.py
def test_all_parsers_implement_interface():
    """All parsers must implement extract_content(path) → str."""
    for parser_class in get_all_parsers():
        assert hasattr(parser_class, 'extract_content')
```

**2. Integration Tests**:
```python
# tests/integration/test_organize_workflow.py
def test_full_organize_workflow():
    """Complete organize workflow from scan to report generation."""
    result = organize_folder(test_folder)
    assert result.files_processed == 50
    assert len(result.categories) >= 3
    assert all_files_moved_correctly()
    assert reports_generated()

# tests/integration/test_restore_capability.py
def test_restore_returns_to_original_state():
    """Restore must return all files to exact original locations."""
    original_state = snapshot_folder_state()
    organize_folder(test_folder)
    restore_folder(test_folder)
    assert folder_matches_snapshot(original_state)
```

**3. Unit Tests** (as needed):
```python
# tests/unit/test_file_scanner.py
def test_scanner_excludes_system_directories():
    """FileScanner must exclude .git, __pycache__, etc."""
    scanner = FileScanner()
    files = scanner.scan(folder_with_system_dirs)
    assert not any('.git' in f.path for f in files)
```

**Test Data Strategy**:
- Fixtures in `tests/fixtures/filetype/` with real sample files
- One file per supported format for format testing
- Mixed collections for integration testing
- Corrupted/invalid files for error handling tests

**CI Integration**:
- GitHub Actions workflow runs all tests on PR
- Docstring audit enforced via custom CI step
- Coverage report generated and tracked (target: 80%+)
- Performance benchmarks run on merge to main

---

## 8. CLI and GUI Interface Design

### Decision: Dual Interface with Shared Core Logic

**Rationale**:
- CLI for power users and automation
- GUI for less technical users
- Shared `fileorg/core/organizer.py` ensures consistency

**CLI Interface** (`fileorg/cli.py`):
```bash
# Standard organization
fileorg /path/to/folder

# Preview mode (no file movement)
fileorg /path/to/folder --preview

# Restore to original structure
fileorg /path/to/folder --restore

# Configuration
fileorg /path/to/folder --backend qualcomm
```

**GUI Interface** (`fileorg/gui/usercli.py`):
- Cross-platform terminal UI (works in Windows/Unix)
- Arrow key navigation for folder selection
- History tracking (recent folders)
- Visual feedback during processing

**Consistency Requirements** (per Constitution):
- Both interfaces call same core functions
- Error messages identical across interfaces
- Progress indicators in both
- Help documentation covers both

**Alternatives Considered**:
1. **Web-based GUI (Flask/FastAPI)**: Rejected - adds complexity, not needed for desktop tool
2. **Native GUI (Qt/Tkinter)**: Deferred to future - terminal UI sufficient for MVP
3. **CLI-only**: Rejected - excludes less technical users

---

## 9. Error Handling and Edge Cases

### Decision: Graceful Degradation with Comprehensive Logging

**Rationale**:
- Single file failure should not stop entire organization
- Users need visibility into what went wrong
- Logs enable debugging and support

**Error Handling Strategy**:

**Recoverable Errors** (log and continue):
- Corrupted file → log error, place in "Unprocessable_Files" category
- Permission denied → log error, skip file
- Locked file → log error, skip file
- Parsing failure → log error, categorize by extension

**Critical Errors** (stop execution):
- Disk full → stop, provide clear error message with remedy
- Backup file write failure → stop, cannot proceed safely
- Invalid target folder → stop, validate input

**Error Message Format** (per Constitution - actionable):
```
❌ Error: Cannot read file 'document.pdf'
   Reason: File is password-protected
   Action: Manually decrypt file and retry, or exclude from organization
```

**Logging Levels**:
- **ERROR**: Critical failures requiring user attention
- **WARNING**: Recoverable issues (skipped files)
- **INFO**: Progress updates, major milestones
- **DEBUG**: Detailed execution trace (for development)

**Error Log Location**: `.backup/errors.log` alongside backup JSON

---

## 10. Documentation and Docstring Standards

### Decision: Google Python Style Guide with CI Enforcement

**Rationale**:
- Google style is widely adopted and readable
- CI enforcement ensures compliance before merge
- Docstrings serve as inline documentation for maintenance

**Docstring Format**:
```python
def organize_folder(folder_path: str, preview: bool = False) -> OrganizationResult:
    """Organizes files in the specified folder based on content analysis.

    Analyzes all files in the folder, extracts content, uses AI to categorize,
    and moves files into semantic folder structure. Generates backup data
    for restoration capability.

    Args:
        folder_path: Absolute path to folder to organize. Must exist and be readable.
        preview: If True, generates organization plan without moving files.

    Returns:
        OrganizationResult containing:
            - files_processed: Number of files analyzed
            - categories: List of category names created
            - errors: List of files that could not be processed

    Raises:
        ValueError: If folder_path does not exist or is not a directory.
        PermissionError: If folder_path is not readable.
        DiskFullError: If insufficient disk space for organization.

    Example:
        >>> result = organize_folder("/Users/name/Downloads", preview=True)
        >>> print(f"Would organize {result.files_processed} files into {len(result.categories)} categories")
    """
```

**CI Pipeline** (`.github/workflows/ci.yml`):
```yaml
- name: Audit Docstrings
  run: |
    python -m pydocstyle fileorg/ --convention=google
    python -m mypy fileorg/ --strict
```

**Documentation Requirements**:
- All public functions/classes must have docstrings
- All modules must have module-level docstrings
- Complex algorithms must include inline comments explaining "why"
- README must be updated when user-facing changes occur

---

## 11. Deployment and Packaging

### Decision: pipx Installation with Entry Point Script

**Rationale**:
- `pipx` provides isolated environment (no dependency conflicts)
- Standard Python packaging with `pyproject.toml`
- Entry point enables `fileorg` command globally

**Package Structure** (from existing `pyproject.toml`):
```toml
[project]
name = "fileorg"
version = "1.0.0"
dependencies = [
    "httpx",           # NPU API client (default)
    "pypdf",           # PDF parsing
    "python-docx",     # Word parsing
    "openpyxl",        # Excel parsing
    "python-pptx",     # PowerPoint parsing
]

[project.optional-dependencies]
non-npu = [
    "torch",                # CPU/GPU inference
    "transformers",         # Hugging Face models
]
dev = [
    "pytest",               # Testing
    "pytest-cov",           # Coverage
    "black",                # Formatting
    "mypy",                 # Type checking
    "flake8",               # Linting
]

[project.scripts]
fileorg = "fileorg.cli:main"
```

**Installation Methods**:
```bash
# End users (recommended)
pipx install git+https://github.com/leoliu5550/QualcommHackathon.git

# Development
git clone ...
pip install -e ".[dev]"

# With non-NPU support
pip install -e ".[non-npu]"
```

**Alternatives Considered**:
1. **Docker container**: Rejected - overkill for CLI tool, limits NPU access
2. **Binary distribution (PyInstaller)**: Deferred - pip installation sufficient for MVP
3. **PyPI package**: Planned but not required for initial release

---

## Summary of Key Decisions

| Area | Decision | Primary Rationale |
|------|----------|-------------------|
| **AI Backend** | Hugging Face + Qualcomm SDK | Hardware acceleration + privacy |
| **Content Parsing** | Format-specific libraries with factory | Proven libraries, extensible design |
| **Architecture** | Pipeline with phase separation | Clear flow, testable, maintainable |
| **Backup/Restore** | JSON path mapping | Simple, sufficient, human-readable |
| **Performance** | Batch processing + lazy loading | Meet 100 files/min target within memory limits |
| **Testing** | Contract-first test pyramid | Interface stability, workflow verification |
| **Interfaces** | Dual CLI + terminal GUI | Power users + accessibility |
| **Error Handling** | Graceful degradation + logging | Single failure doesn't stop process |
| **Documentation** | Google-style docstrings with CI | Maintainability + enforced quality |
| **Deployment** | pipx with optional dependencies | Isolated environment, easy installation |

---

## Research Complete ✅

All technical decisions documented. No NEEDS CLARIFICATION items remain. Ready to proceed to Phase 1: Design artifacts (data-model.md, contracts/, quickstart.md).
