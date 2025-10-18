# QuickStart Guide: FileOrg Development

**Feature**: 001-ai-content-organization
**Date**: 2025-10-18
**Audience**: Developers implementing the FileOrg AI-powered file organization system

## Overview

This guide provides a step-by-step walkthrough for implementing FileOrg's AI-powered file organization feature. Follow this sequence to build the system incrementally with tests first.

---

## Prerequisites

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/leoliu5550/QualcommHackathon.git
cd QualcommHackathon

# Checkout feature branch
git checkout 001-ai-content-organization

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,non-npu]"

# Verify installation
pytest --version
black --version
mypy --version
```

### Required Tools

- Python 3.11+
- Git
- pytest (testing)
- black (formatting)
- mypy (type checking)
- flake8 (linting)

---

## Implementation Roadmap

### Phase 1: Core Data Structures ✅ (Design Complete)

**Artifacts Ready**:
- Data model defined in `specs/001-ai-content-organization/data-model.md`
- CLI interface contract in `contracts/cli-interface.md`
- Parser interface contract in `contracts/parser-interface.md`

**Next Steps**: Implement data classes with tests

---

### Phase 2: File Scanner (User Story 6 - P1)

**Goal**: Discover files in target folder

**Test First** (`tests/contract/test_file_scanner.py`):
```python
def test_scanner_finds_all_files_in_folder():
    """Scanner must discover all files recursively."""
    scanner = FileScanner()
    files = scanner.scan(Path("tests/fixtures/sample_folder"))
    assert len(files) >= 10

def test_scanner_excludes_system_directories():
    """Scanner must exclude .git, __pycache__, etc."""
    scanner = FileScanner()
    files = scanner.scan(Path("tests/fixtures/with_system_dirs"))
    assert not any('.git' in str(f.path) for f in files)
    assert not any('__pycache__' in str(f.path) for f in files)

def test_scanner_handles_permission_errors_gracefully():
    """Scanner must skip files it cannot read."""
    scanner = FileScanner()
    files = scanner.scan(Path("tests/fixtures/restricted_folder"))
    # Should not raise exception, just skip
    assert isinstance(files, list)
```

**Implementation** (`fileorg/scanner/core.py`):
```python
from pathlib import Path
from typing import List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FileMetadata:
    """Metadata for a discovered file."""
    path: Path
    name: str
    extension: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    is_readable: bool

EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".backup", ".reports"}

class FileScanner:
    """Discovers files in folder recursively."""

    def scan(self, folder_path: Path) -> List[FileMetadata]:
        """Scan folder and return all file metadata.

        Args:
            folder_path: Root folder to scan

        Returns:
            List of FileMetadata for all discoverable files
        """
        files = []
        for item in folder_path.rglob("*"):
            # Skip excluded directories
            if any(excluded in str(item) for excluded in EXCLUDED_DIRS):
                continue

            # Skip non-files
            if not item.is_file():
                continue

            # Try to read metadata
            try:
                stat = item.stat()
                files.append(FileMetadata(
                    path=item.absolute(),
                    name=item.name,
                    extension=item.suffix.lower(),
                    size_bytes=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_ctime),
                    modified_at=datetime.fromtimestamp(stat.st_mtime),
                    is_readable=item.exists() and item.is_file()
                ))
            except (PermissionError, OSError):
                # Skip files we cannot access
                continue

        return files
```

**Validation**:
```bash
pytest tests/contract/test_file_scanner.py -v
black fileorg/scanner/core.py
mypy fileorg/scanner/core.py
```

---

### Phase 3: Content Parsers (User Story 6 - P1)

**Goal**: Extract content from multiple file formats

**Test First** (`tests/contract/test_parser_contracts.py`):
```python
def test_pdf_parser_extracts_text():
    """PDF parser must extract text content."""
    parser = PDFParser()
    result = parser.extract_content(Path("tests/fixtures/filetype/sample.pdf"))
    assert result.success is True
    assert len(result.content) > 0
    assert result.word_count > 0

def test_word_parser_extracts_text():
    """Word parser must extract text from DOCX."""
    parser = WordParser()
    result = parser.extract_content(Path("tests/fixtures/filetype/sample.docx"))
    assert result.success is True
    assert len(result.content) > 0

def test_parser_respects_max_words_limit():
    """Parsers must limit content to max_words."""
    parser = TextParser()
    result = parser.extract_content(
        Path("tests/fixtures/filetype/long_text.txt"),
        max_words=100
    )
    assert result.word_count <= 100

def test_corrupted_file_returns_error():
    """Parser must handle corrupted files gracefully."""
    parser = PDFParser()
    result = parser.extract_content(Path("tests/fixtures/corrupted.pdf"))
    assert result.success is False
    assert result.error_message is not None
```

**Implementation** (`fileorg/parsers/pdf_parser.py`):
```python
from pathlib import Path
from pypdf import PdfReader
from .base import BaseParser, ParseResult

class PDFParser(BaseParser):
    """Extract text content from PDF files."""

    @property
    def supported_extensions(self) -> set[str]:
        return {".pdf"}

    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions

    def extract_content(self, file_path: Path, max_words: int = 2000) -> ParseResult:
        """Extract text from PDF.

        Args:
            file_path: Path to PDF file
            max_words: Maximum words to extract

        Returns:
            ParseResult with extracted text or error
        """
        try:
            reader = PdfReader(str(file_path))
            text_parts = []
            word_count = 0

            for page in reader.pages:
                page_text = page.extract_text()
                words = page_text.split()

                for word in words:
                    if word_count >= max_words:
                        break
                    text_parts.append(word)
                    word_count += 1

                if word_count >= max_words:
                    break

            content = " ".join(text_parts)
            return ParseResult(
                success=True,
                content=content,
                word_count=word_count,
                parser_name=self.parser_name
            )

        except Exception as e:
            return ParseResult(
                success=False,
                content="",
                word_count=0,
                error_message=f"PDF parsing failed: {str(e)}",
                parser_name=self.parser_name
            )
```

**Repeat for Other Parsers**: Word, Excel, PowerPoint, HTML, JSON, XML, CSV

**Parser Factory** (`fileorg/parsers/factory.py`):
```python
from pathlib import Path
from typing import Optional, List
from .base import BaseParser
from .pdf_parser import PDFParser
from .word_parser import WordParser
# ... import all parsers

class ParserFactory:
    """Factory for selecting appropriate file parser."""

    def __init__(self):
        self._parsers: List[BaseParser] = [
            PDFParser(),
            WordParser(),
            ExcelParser(),
            PowerPointParser(),
            TextParser(),
            HTMLParser(),
            JSONParser(),
            XMLParser(),
            CSVParser(),
        ]

    def get_parser(self, file_path: Path) -> Optional[BaseParser]:
        """Get parser for file based on extension.

        Args:
            file_path: Path to file

        Returns:
            Parser that can handle file, or None
        """
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser
        return None
```

**Validation**:
```bash
pytest tests/contract/test_parser_contracts.py -v
pytest tests/unit/test_content_extraction.py -v
```

---

### Phase 4: AI Classification (User Story 1 - P1)

**Goal**: Analyze content and generate categories using AI

**Test First** (`tests/contract/test_ai_backend_api.py`):
```python
def test_classifier_generates_category_name():
    """Classifier must generate semantic category from content."""
    classifier = FileClassifier(backend="local")  # Use local for testing
    category = classifier.classify_content("Invoice #12345\nAmount: $1000")
    assert category is not None
    assert len(category.name) > 0
    assert "_" in category.name  # e.g., "Financial_Documents"

def test_classifier_groups_similar_files():
    """Classifier must group semantically similar files."""
    classifier = FileClassifier(backend="local")
    files = [
        FileContent(content="Invoice #1", ...),
        FileContent(content="Invoice #2", ...),
        FileContent(content="Receipt for payment", ...),
    ]
    categories = classifier.classify_batch(files)
    # All should go to same category (Financial)
    assert len(categories) == 1
```

**Implementation** (`fileorg/ai/classifier.py`):
```python
from typing import List, Dict
from pathlib import Path
from transformers import pipeline
from .config import LLM_CONFIG
from .prompt_engine.builder import PromptBuilder

class FileClassifier:
    """AI-powered file content classifier."""

    def __init__(self, backend: str = "local"):
        self.backend = backend
        if backend == "local":
            self.model = pipeline("text-generation", model="gpt2")  # Example
        else:
            # Qualcomm NPU backend
            self.api_url = LLM_CONFIG["qualcomm_api_url"]

    def classify_content(self, content: str) -> Category:
        """Generate category for file content.

        Args:
            content: Extracted file content

        Returns:
            Category with generated name
        """
        prompt = PromptBuilder.build_classification_prompt(content)

        if self.backend == "local":
            response = self.model(prompt, max_length=50)[0]["generated_text"]
        else:
            response = self._call_qualcomm_api(prompt)

        category_name = self._extract_category_name(response)
        return Category(
            name=category_name,
            file_paths=[],
            confidence_score=0.9
        )

    def classify_batch(self, files: List[FileContent]) -> List[Category]:
        """Classify multiple files into categories."""
        # Group files with similar content into categories
        # Implementation details...
```

**Validation**:
```bash
pytest tests/contract/test_ai_backend_api.py -v
pytest tests/integration/test_ai_classification.py -v
```

---

### Phase 5: File Organization (User Story 1 - P1)

**Goal**: Move files to organized structure with backup

**Test First** (`tests/integration/test_organize_workflow.py`):
```python
def test_organize_creates_category_folders():
    """Organize must create semantic category folders."""
    organizer = FileOrganizer()
    result = organizer.organize(Path("tests/fixtures/sample_folder"))
    assert result.files_moved > 0
    assert len(result.categories_created) > 0

def test_organize_moves_files_to_correct_categories():
    """Files must be moved to semantically appropriate folders."""
    organizer = FileOrganizer()
    organizer.organize(Path("tests/fixtures/sample_folder"))
    # Check that invoice.pdf is in Financial folder
    assert (Path("tests/fixtures/sample_folder/Financial_Documents/invoice.pdf").exists())

def test_organize_creates_backup_manifest():
    """Backup manifest must be created with all file mappings."""
    organizer = FileOrganizer()
    organizer.organize(Path("tests/fixtures/sample_folder"))
    backup_path = Path("tests/fixtures/sample_folder/.backup/file_paths.json")
    assert backup_path.exists()
    # Validate JSON structure
```

**Implementation** (`fileorg/core/organizer.py`):
```python
from pathlib import Path
from typing import List
from ..scanner.core import FileScanner
from ..parsers.factory import ParserFactory
from ..ai.classifier import FileClassifier
from ..data_model import OrganizationResult, BackupManifest

class FileOrganizer:
    """Orchestrates the file organization workflow."""

    def __init__(self):
        self.scanner = FileScanner()
        self.parser_factory = ParserFactory()
        self.classifier = FileClassifier()

    def organize(self, folder_path: Path, preview: bool = False) -> OrganizationResult:
        """Organize files in folder based on content analysis.

        Args:
            folder_path: Folder to organize
            preview: If True, don't move files (preview only)

        Returns:
            OrganizationResult with outcome details
        """
        # Phase 1: Scan files
        files = self.scanner.scan(folder_path)

        # Phase 2: Extract content
        file_contents = []
        for file_meta in files:
            parser = self.parser_factory.get_parser(file_meta.path)
            if parser:
                result = parser.extract_content(file_meta.path)
                if result.success:
                    file_contents.append(FileContent(file_meta, result.content))

        # Phase 3: Classify
        categories = self.classifier.classify_batch(file_contents)

        # Phase 4: Create backup (before moving)
        backup_manifest = self._create_backup_manifest(categories, folder_path)
        backup_path = folder_path / ".backup" / "file_paths.json"
        backup_path.parent.mkdir(exist_ok=True)
        self._save_backup(backup_manifest, backup_path)

        # Phase 5: Move files (unless preview mode)
        files_moved = 0
        if not preview:
            for category in categories:
                category_folder = folder_path / category.name
                category_folder.mkdir(exist_ok=True)
                for file_path in category.file_paths:
                    dest = category_folder / Path(file_path).name
                    Path(file_path).rename(dest)
                    files_moved += 1

        # Phase 6: Generate reports
        # ... report generation ...

        return OrganizationResult(
            files_processed=len(files),
            files_moved=files_moved,
            categories_created=[c.name for c in categories],
            preview_mode=preview
        )
```

**Validation**:
```bash
pytest tests/integration/test_organize_workflow.py -v
```

---

### Phase 6: Preview Mode (User Story 2 - P2)

**Test First** (`tests/integration/test_preview_mode.py`):
```python
def test_preview_mode_does_not_move_files():
    """Preview mode must NOT move any files."""
    original_files = list_all_files("tests/fixtures/sample_folder")
    organizer = FileOrganizer()
    organizer.organize(Path("tests/fixtures/sample_folder"), preview=True)
    current_files = list_all_files("tests/fixtures/sample_folder")
    assert original_files == current_files  # Files unchanged

def test_preview_generates_reports():
    """Preview must generate reports showing proposed structure."""
    organizer = FileOrganizer()
    result = organizer.organize(Path("tests/fixtures/sample_folder"), preview=True)
    assert result.preview_mode is True
    # Check reports exist
```

**Implementation**: Update `FileOrganizer.organize()` to skip file movement when `preview=True`

---

### Phase 7: Restore Capability (User Story 3 - P2)

**Test First** (`tests/contract/test_backup_restore.py`):
```python
def test_restore_returns_files_to_original_locations():
    """Restore must return all files to pre-organization state."""
    folder = Path("tests/fixtures/sample_folder")
    original_state = snapshot_folder_state(folder)

    organizer = FileOrganizer()
    organizer.organize(folder)

    restorer = FileRestorer()
    restorer.restore(folder)

    current_state = snapshot_folder_state(folder)
    assert original_state == current_state
```

**Implementation** (`fileorg/restore/restore.py`):
```python
from pathlib import Path
import json
from ..data_model import BackupManifest, RestoreResult

class FileRestorer:
    """Restores folder to original structure using backup."""

    def restore(self, folder_path: Path) -> RestoreResult:
        """Restore folder to pre-organization state.

        Args:
            folder_path: Folder to restore

        Returns:
            RestoreResult with outcome
        """
        backup_path = folder_path / ".backup" / "file_paths.json"
        if not backup_path.exists():
            raise ValueError("No backup found - folder was not organized")

        # Load backup
        with open(backup_path) as f:
            backup_data = json.load(f)
        manifest = BackupManifest.from_dict(backup_data)

        # Reverse all file movements
        for record in manifest.records:
            new_path = Path(record.new_path)
            original_path = Path(record.original_path)
            if new_path.exists():
                new_path.rename(original_path)

        return RestoreResult(files_restored=len(manifest.records))
```

---

### Phase 8: CLI Interface (User Story 1, 2, 3)

**Test First** (`tests/contract/test_cli_interface.py`):
```python
def test_cli_organizes_folder():
    """CLI must accept folder path and organize."""
    result = run_cli(["fileorg", "tests/fixtures/sample_folder"])
    assert result.exit_code == 0

def test_cli_preview_flag():
    """CLI --preview flag must run preview mode."""
    result = run_cli(["fileorg", "tests/fixtures/sample_folder", "--preview"])
    assert result.exit_code == 0
    # Verify files not moved

def test_cli_restore_flag():
    """CLI --restore flag must restore folder."""
    result = run_cli(["fileorg", "tests/fixtures/sample_folder", "--restore"])
    assert result.exit_code == 0
```

**Implementation** (`fileorg/cli/cli.py`):
```python
import click
from pathlib import Path
from ..core.organizer import FileOrganizer
from ..restore.restore import FileRestorer

@click.command()
@click.argument("folder", type=click.Path(exists=True))
@click.option("--preview", is_flag=True, help="Preview without moving files")
@click.option("--restore", is_flag=True, help="Restore to original structure")
@click.option("--backend", default="qualcomm", help="AI backend: qualcomm or local")
def main(folder: str, preview: bool, restore: bool, backend: str):
    """FileOrg - AI-Powered File Organization."""
    folder_path = Path(folder).absolute()

    if restore:
        restorer = FileRestorer()
        result = restorer.restore(folder_path)
        click.echo(f"✓ Restored {result.files_restored} files")
        return

    organizer = FileOrganizer(backend=backend)
    result = organizer.organize(folder_path, preview=preview)

    mode_text = "Preview complete" if preview else "Organization complete"
    click.echo(f"✓ {mode_text}!")
    click.echo(f"  Files processed: {result.files_processed}")
    click.echo(f"  Categories: {len(result.categories_created)}")
```

---

### Phase 9: Report Generation (User Story 4 - P3)

**Test First** (`tests/unit/test_report_generation.py`):
```python
def test_generate_html_tree_report():
    """HTML tree report must show folder structure."""
    reporter = ReportGenerator()
    result = OrganizationResult(...)
    html_path = reporter.generate_html_tree(result, Path("output"))
    assert html_path.exists()
    # Validate HTML structure

def test_generate_markdown_summary():
    """Markdown summary must include statistics."""
    reporter = ReportGenerator()
    result = OrganizationResult(...)
    md_path = reporter.generate_markdown_summary(result, Path("output"))
    content = md_path.read_text()
    assert "Files processed:" in content
    assert "Categories created:" in content
```

**Implementation** (`fileorg/reporter/generator.py`): Generate HTML/Markdown reports

---

## Testing Strategy

### Test Execution Order

```bash
# 1. Contract tests (interfaces)
pytest tests/contract/ -v

# 2. Unit tests (individual components)
pytest tests/unit/ -v

# 3. Integration tests (workflows)
pytest tests/integration/ -v

# 4. Coverage report
pytest --cov=fileorg --cov-report=html
```

### Test Data Setup

```bash
# Create test fixtures
mkdir -p tests/fixtures/filetype
mkdir -p tests/fixtures/sample_folder

# Add sample files for each format
# PDF, DOCX, XLSX, PPTX, TXT, HTML, JSON, XML, CSV
```

---

## Development Workflow

### Daily Workflow

1. **Pull latest changes**:
   ```bash
   git pull origin 001-ai-content-organization
   ```

2. **Write test for next feature**:
   ```bash
   # Edit test file
   pytest tests/contract/test_*.py::test_new_feature -v
   # Test should FAIL (Red)
   ```

3. **Implement feature**:
   ```bash
   # Edit implementation file
   pytest tests/contract/test_*.py::test_new_feature -v
   # Test should PASS (Green)
   ```

4. **Refactor if needed**:
   ```bash
   # Clean up code
   pytest tests/contract/ -v  # All tests still pass
   ```

5. **Format and lint**:
   ```bash
   black fileorg/
   mypy fileorg/
   flake8 fileorg/
   ```

6. **Commit**:
   ```bash
   git add .
   git commit -m "feat(organizer): implement file organization workflow"
   ```

---

## Common Issues & Solutions

### Issue 1: Import Errors

**Problem**: `ModuleNotFoundError: No module named 'fileorg'`

**Solution**:
```bash
pip install -e .
```

### Issue 2: Test Fixtures Missing

**Problem**: Tests fail because fixture files don't exist

**Solution**:
```bash
# Create test data
mkdir -p tests/fixtures/filetype
# Add sample files manually or use generator script
```

### Issue 3: Hugging Face Model Download Slow

**Problem**: First run downloads model, takes time

**Solution**:
```bash
# Pre-download model
python -c "from transformers import pipeline; pipeline('text-generation', model='gpt2')"
```

---

## Code Quality Checklist

Before committing, verify:

- [ ] All tests pass (`pytest`)
- [ ] Code formatted (`black fileorg/`)
- [ ] Type hints validated (`mypy fileorg/`)
- [ ] No linting errors (`flake8 fileorg/`)
- [ ] Docstrings present (Google style)
- [ ] Coverage maintained or improved
- [ ] Commit message follows conventions

---

## Next Steps

After completing basic implementation:

1. **Performance optimization** (User Story 5 - P3)
2. **GUI implementation** (`fileorg/gui/usercli.py`)
3. **Documentation updates** (README, API docs)
4. **Integration with CI/CD** (GitHub Actions)

---

## Resources

- **Specification**: `specs/001-ai-content-organization/spec.md`
- **Data Model**: `specs/001-ai-content-organization/data-model.md`
- **Contracts**: `specs/001-ai-content-organization/contracts/`
- **Constitution**: `.specify/memory/constitution.md`

---

## Questions?

- Check existing codebase for patterns
- Review data model and contracts for interface definitions
- Consult constitution for quality standards
- Ask team for clarifications on ambiguous requirements

---

**Ready to Code!** Start with Phase 2 (File Scanner) and work through each phase sequentially, following TDD principles. Good luck! 🚀
