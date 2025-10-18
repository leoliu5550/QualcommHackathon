# Parser Interface Contract

**Feature**: 001-ai-content-organization
**Date**: 2025-10-18
**Version**: 1.0

## Overview

This contract defines the interface that all file content parsers must implement. Parsers extract text content from specific file formats for AI analysis.

---

## Core Interface

### BaseParser Abstract Class

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

@dataclass
class ParseResult:
    """Result of content extraction from a file."""
    success: bool
    content: str
    word_count: int
    error_message: Optional[str] = None
    parser_name: str = ""

class BaseParser(ABC):
    """Abstract base class for all file format parsers."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.

        Args:
            file_path: Path to file to check

        Returns:
            True if parser supports this file format

        Contract:
            - MUST return True only for supported extensions
            - MUST NOT raise exceptions
            - MUST complete in <10ms
        """
        pass

    @abstractmethod
    def extract_content(self, file_path: Path, max_words: int = 2000) -> ParseResult:
        """Extract text content from file.

        Args:
            file_path: Absolute path to file
            max_words: Maximum words to extract (default 2000)

        Returns:
            ParseResult with extracted content or error

        Contract:
            - MUST return ParseResult (never None)
            - MUST handle errors gracefully (no exceptions)
            - MUST limit content to max_words
            - MUST set success=False if extraction fails
            - MUST provide error_message when success=False
            - MUST complete in <5 seconds per file
        """
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Return set of file extensions this parser supports.

        Returns:
            Set of extensions like {".pdf", ".docx"}

        Contract:
            - MUST include leading dot in extensions
            - MUST be lowercase
            - MUST be immutable (return copy or tuple)
        """
        pass

    @property
    def parser_name(self) -> str:
        """Return human-readable parser name."""
        return self.__class__.__name__
```

---

## Contract Specifications

### P1: PDF Parser Contract

**Parser Name**: `PDFParser`

**Supported Extensions**: `{".pdf"}`

**Method**: `extract_content(file_path, max_words=2000) -> ParseResult`

**Preconditions**:
- File exists and is readable
- File has `.pdf` extension
- File is not password-protected (or error handled)

**Postconditions**:
- Returns ParseResult with extracted text
- Content limited to max_words
- success=True if extraction succeeded

**Error Handling**:
```python
# Password-protected PDF
ParseResult(
    success=False,
    content="",
    word_count=0,
    error_message="PDF is password-protected",
    parser_name="PDFParser"
)

# Corrupted PDF
ParseResult(
    success=False,
    content="",
    word_count=0,
    error_message="PDF file appears corrupted or invalid",
    parser_name="PDFParser"
)
```

**Performance Contract**:
- Extract content in <5 seconds for files up to 100MB
- Memory usage <200MB per file

---

### P2: Word Document Parser Contract

**Parser Name**: `WordParser`

**Supported Extensions**: `{".docx", ".doc"}`

**Method**: `extract_content(file_path, max_words=2000) -> ParseResult`

**Preconditions**:
- File exists and is readable
- File has `.docx` or `.doc` extension

**Postconditions**:
- Returns ParseResult with extracted text from paragraphs
- Excludes headers/footers (content focus)
- Content limited to max_words

**Error Handling**:
```python
# Corrupted DOCX
ParseResult(
    success=False,
    content="",
    word_count=0,
    error_message="Word document is corrupted or invalid format",
    parser_name="WordParser"
)
```

**Performance Contract**:
- Extract content in <3 seconds for files up to 50MB

---

### P3: Excel Parser Contract

**Parser Name**: `ExcelParser`

**Supported Extensions**: `{".xlsx", ".xls"}`

**Method**: `extract_content(file_path, max_words=2000) -> ParseResult`

**Preconditions**:
- File exists and is readable
- File has `.xlsx` or `.xls` extension

**Postconditions**:
- Returns ParseResult with cell values as text
- Extracts from first N rows until max_words reached
- Skips empty cells

**Content Format**:
```
Sheet: Financial Data
Column A: Invoice, Column B: Amount, Column C: Date
Row 1: INV-001, 1234.56, 2025-01-15
Row 2: INV-002, 2345.67, 2025-01-16
...
```

**Performance Contract**:
- Extract content in <5 seconds for spreadsheets up to 10,000 rows

---

### P4: PowerPoint Parser Contract

**Parser Name**: `PowerPointParser`

**Supported Extensions**: `{".pptx", ".ppt"}`

**Method**: `extract_content(file_path, max_words=2000) -> ParseResult`

**Preconditions**:
- File exists and is readable
- File has `.pptx` or `.ppt` extension

**Postconditions**:
- Returns ParseResult with text from slides
- Extracts slide titles and content
- Skips images/shapes (text only)

**Content Format**:
```
Slide 1: Project Overview
Content: This presentation covers...

Slide 2: Q1 Results
Content: Revenue increased by...
```

**Performance Contract**:
- Extract content in <3 seconds for presentations up to 100 slides

---

### P5: Text File Parser Contract

**Parser Name**: `TextParser`

**Supported Extensions**: `{".txt", ".md", ".log"}`

**Method**: `extract_content(file_path, max_words=2000) -> ParseResult`

**Preconditions**:
- File exists and is readable
- File is plain text (UTF-8 or ASCII)

**Postconditions**:
- Returns ParseResult with file content
- Handles different encodings gracefully
- Content limited to max_words

**Error Handling**:
```python
# Binary file treated as text
ParseResult(
    success=False,
    content="",
    word_count=0,
    error_message="File appears to be binary, not plain text",
    parser_name="TextParser"
)
```

**Performance Contract**:
- Extract content in <1 second for files up to 10MB

---

### P6: HTML Parser Contract

**Parser Name**: `HTMLParser`

**Supported Extensions**: `{".html", ".htm"}`

**Method**: `extract_content(file_path, max_words=2000) -> ParseResult`

**Preconditions**:
- File exists and is readable
- File contains HTML markup

**Postconditions**:
- Returns ParseResult with text content (no HTML tags)
- Strips JavaScript, CSS, and markup
- Preserves readable text only

**Performance Contract**:
- Extract content in <2 seconds for files up to 5MB

---

### P7: JSON Parser Contract

**Parser Name**: `JSONParser`

**Supported Extensions**: `{".json"}`

**Method**: `extract_content(file_path, max_words=2000) -> ParseResult`

**Preconditions**:
- File exists and is readable
- File contains valid JSON

**Postconditions**:
- Returns ParseResult with JSON structure as readable text
- Extracts keys and values
- Formats nested structures readably

**Content Format**:
```
JSON Structure:
Key: name, Value: John Doe
Key: email, Value: john@example.com
Key: orders, Value: [Array with 3 items]
  orders[0].id: 12345
  orders[0].amount: 100.50
```

**Error Handling**:
```python
# Invalid JSON
ParseResult(
    success=False,
    content="",
    word_count=0,
    error_message="Invalid JSON syntax",
    parser_name="JSONParser"
)
```

---

### P8: XML Parser Contract

**Parser Name**: `XMLParser`

**Supported Extensions**: `{".xml"}`

**Method**: `extract_content(file_path, max_words=2000) -> ParseResult`

**Preconditions**:
- File exists and is readable
- File contains valid XML

**Postconditions**:
- Returns ParseResult with XML content as readable text
- Extracts tag names and text content
- Skips attributes (focus on content)

---

### P9: CSV Parser Contract

**Parser Name**: `CSVParser`

**Supported Extensions**: `{".csv"}`

**Method**: `extract_content(file_path, max_words=2000) -> ParseResult`

**Preconditions**:
- File exists and is readable
- File contains comma-separated values

**Postconditions**:
- Returns ParseResult with tabular data as text
- Includes headers if present
- Extracts first N rows until max_words reached

**Content Format**:
```
CSV Data (3 columns, 127 rows):
Headers: Name, Email, Date
Row 1: John Doe, john@example.com, 2025-01-15
Row 2: Jane Smith, jane@example.com, 2025-01-16
...
```

---

## Parser Factory Contract

### ParserFactory Class

```python
class ParserFactory:
    """Factory for selecting appropriate parser based on file extension."""

    def __init__(self):
        self._parsers: list[BaseParser] = []

    def register_parser(self, parser: BaseParser) -> None:
        """Register a parser with the factory.

        Contract:
            - MUST store parser for later use
            - MUST allow multiple parsers for same extension (first wins)
        """
        pass

    def get_parser(self, file_path: Path) -> Optional[BaseParser]:
        """Get appropriate parser for file.

        Args:
            file_path: Path to file

        Returns:
            Parser that can handle file, or None if unsupported

        Contract:
            - MUST return first parser where can_parse() returns True
            - MUST return None if no parser supports file
            - MUST complete in <10ms
        """
        pass

    def supported_extensions(self) -> set[str]:
        """Get all supported file extensions across all parsers.

        Returns:
            Set of all supported extensions

        Contract:
            - MUST include extensions from all registered parsers
            - MUST be lowercase with leading dots
        """
        pass
```

---

## Contract Testing

**Test Implementation Location**: `tests/contract/test_parser_contracts.py`

**Required Tests**:

```python
def test_all_parsers_implement_interface():
    """All parsers must implement BaseParser interface."""
    for parser_class in get_all_parser_classes():
        parser = parser_class()
        assert isinstance(parser, BaseParser)
        assert hasattr(parser, 'can_parse')
        assert hasattr(parser, 'extract_content')
        assert hasattr(parser, 'supported_extensions')

def test_extract_content_never_raises_exceptions():
    """Parsers must handle errors gracefully, never raise."""
    parser = PDFParser()
    result = parser.extract_content(Path("/nonexistent/file.pdf"))
    assert isinstance(result, ParseResult)
    assert result.success is False

def test_extract_content_respects_max_words():
    """Parsers must limit content to max_words parameter."""
    parser = TextParser()
    result = parser.extract_content(large_text_file, max_words=100)
    assert result.word_count <= 100

def test_can_parse_completes_quickly():
    """can_parse() must complete in under 10ms."""
    parser = PDFParser()
    start = time.time()
    parser.can_parse(Path("test.pdf"))
    duration = time.time() - start
    assert duration < 0.010  # 10ms

def test_extract_content_completes_within_timeout():
    """extract_content() must complete in under 5 seconds."""
    parser = PDFParser()
    start = time.time()
    parser.extract_content(typical_pdf_file)
    duration = time.time() - start
    assert duration < 5.0

def test_parser_factory_returns_correct_parser():
    """Factory must return appropriate parser for file extension."""
    factory = ParserFactory()
    # ... register parsers ...
    parser = factory.get_parser(Path("document.pdf"))
    assert isinstance(parser, PDFParser)

def test_parse_result_has_error_message_when_failed():
    """Failed ParseResult must include error_message."""
    result = ParseResult(success=False, content="", word_count=0)
    assert result.error_message is not None
```

---

## Performance Benchmarks

**Benchmark Location**: `tests/benchmark/test_parser_performance.py`

| Parser | File Size | Max Time | Max Memory |
|--------|-----------|----------|------------|
| PDF | 100MB | 5 seconds | 200MB |
| Word | 50MB | 3 seconds | 150MB |
| Excel | 10k rows | 5 seconds | 100MB |
| PowerPoint | 100 slides | 3 seconds | 150MB |
| Text | 10MB | 1 second | 50MB |
| HTML | 5MB | 2 seconds | 50MB |
| JSON | 5MB | 1 second | 50MB |
| XML | 5MB | 2 seconds | 50MB |
| CSV | 10k rows | 2 seconds | 50MB |

---

## Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| PARSE_SUCCESS | Content extracted successfully | - |
| PARSE_FILE_NOT_FOUND | File does not exist | /path/to/missing.pdf |
| PARSE_PERMISSION_DENIED | Cannot read file | /root/protected.pdf |
| PARSE_CORRUPTED | File is corrupted | Truncated PDF |
| PARSE_PASSWORD_PROTECTED | File requires password | Encrypted PDF |
| PARSE_INVALID_FORMAT | File format invalid | Binary file with .txt extension |
| PARSE_TIMEOUT | Extraction took too long | Very large file |

---

## Parser Contract Version History

- **v1.0** (2025-10-18): Initial contract definition
