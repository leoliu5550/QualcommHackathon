# Application Layer Interfaces Contract

**Feature**: DEV-docs/create-spec
**Date**: 2025-10-19
**Version**: 1.0

## Overview

This contract defines the interfaces for external services that the application layer depends on. These interfaces are defined in the application layer and implemented by the infrastructure layer, following the Dependency Inversion Principle.

---

## IAIBackend Interface

**Location**: `src/fileorg/application/interfaces/ai_backend.py`

**Purpose**: Abstract AI model inference for content classification

```python
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

@dataclass
class ClassificationRequest:
    """Request for AI classification."""
    texts: List[str]              # File contents to classify
    max_categories: int = 15       # Maximum number of categories
    language: str = "auto"         # Language hint or "auto-detect"

@dataclass
class CategoryPrediction:
    """Single category prediction from AI."""
    name: str                      # Category name (e.g., "Financial_Documents")
    description: str               # Category description
    file_indices: List[int]        # Indices of files belonging to this category
    confidence: float              # Confidence score 0.0-1.0

@dataclass
class ClassificationResponse:
    """Response from AI classification."""
    categories: List[CategoryPrediction]
    processing_time_ms: float
    model_name: str

class IAIBackend(ABC):
    """AI backend interface for content classification.

    Implementations:
    - QualcommNPUBackend: Uses Qualcomm NPU for hardware acceleration
    - LocalBackend: Uses local CPU/GPU with transformers library
    - MockBackend: Returns fake data for testing
    """

    @abstractmethod
    def classify(self, request: ClassificationRequest) -> ClassificationResponse:
        """Classify file contents into semantic categories.

        Args:
            request: Classification request with texts and parameters

        Returns:
            ClassificationResponse with predicted categories

        Raises:
            AIBackendError: If classification fails
            BackendUnavailableError: If backend is not accessible

        Contract:
            - Must complete within 500ms per file on average
            - Must return 5-15 categories
            - Category names must be valid folder names (no special chars)
            - Confidence scores must be between 0.0 and 1.0
            - file_indices must reference valid input text indices
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if backend is available and responding.

        Returns:
            True if backend is healthy

        Contract:
            - Must complete within 2 seconds
            - Must NOT raise exceptions (return False on error)
        """
        pass

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return human-readable backend name.

        Returns:
            Backend identifier (e.g., "Qualcomm NPU", "Local CPU")
        """
        pass
```

---

## IParserFactory Interface

**Location**: `src/fileorg/application/interfaces/parser.py`

**Purpose**: Abstract file content extraction

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from enum import Enum

class ExtractionStatus(Enum):
    """Status of content extraction."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class ParseResult:
    """Result of parsing a file."""
    success: bool
    content: str
    word_count: int
    extraction_status: ExtractionStatus
    error_message: Optional[str] = None
    parser_name: str = ""

class IParser(ABC):
    """Base interface for file parsers."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the file.

        Contract:
            - Must complete in <10ms
            - Must NOT raise exceptions
            - Must check file extension only (not content)
        """
        pass

    @abstractmethod
    def parse(self, file_path: Path, max_words: int = 2000) -> ParseResult:
        """Extract content from file.

        Args:
            file_path: Absolute path to file
            max_words: Maximum words to extract

        Returns:
            ParseResult with content or error

        Contract:
            - Must NEVER raise exceptions
            - Must set success=False on errors
            - Must limit content to max_words
            - Must complete in <5 seconds per file
        """
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Return supported file extensions.

        Returns:
            Set of extensions like {".pdf", ".docx"}

        Contract:
            - Extensions must be lowercase
            - Extensions must include leading dot
        """
        pass

class IParserFactory(ABC):
    """Factory for getting appropriate parser for a file."""

    @abstractmethod
    def get_parser(self, file_path: Path) -> Optional[IParser]:
        """Get parser for file.

        Args:
            file_path: Path to file

        Returns:
            Parser instance or None if unsupported

        Contract:
            - Must return None if no parser supports file
            - Must return first matching parser
            - Must complete in <10ms
        """
        pass

    @abstractmethod
    def register_parser(self, parser: IParser) -> None:
        """Register a new parser.

        Args:
            parser: Parser instance to register

        Contract:
            - Must allow duplicate parsers for same extension
            - Later registrations have lower priority
        """
        pass

    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Get all supported extensions.

        Returns:
            Set of all supported extensions across all parsers
        """
        pass
```

---

## IReportGenerator Interface

**Location**: `src/fileorg/application/interfaces/report_generator.py`

**Purpose**: Abstract report generation

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from dataclasses import dataclass
from ..domain.models.organization import OrganizationResult
from ..domain.models.category import Category

@dataclass
class ReportRequest:
    """Request to generate reports."""
    result: OrganizationResult
    categories: List[Category]
    output_dir: Path
    formats: List[str] = None  # ["html", "markdown", "json"] or None for all

@dataclass
class GeneratedReport:
    """Information about a generated report."""
    format: str               # "html", "markdown", "json"
    file_path: Path          # Path to generated report
    size_bytes: int          # File size

@dataclass
class ReportResponse:
    """Response from report generation."""
    success: bool
    reports: List[GeneratedReport]
    error_message: Optional[str] = None

class IReportGenerator(ABC):
    """Report generator interface."""

    @abstractmethod
    def generate(self, request: ReportRequest) -> ReportResponse:
        """Generate organization reports.

        Args:
            request: Report generation request

        Returns:
            ReportResponse with paths to generated reports

        Raises:
            ReportGenerationError: If generation fails

        Contract:
            - Must create output_dir if it doesn't exist
            - Must overwrite existing reports without error
            - Must generate all requested formats
            - HTML report must include visual tree structure
            - Markdown report must be human-readable
            - JSON report must be machine-parseable
        """
        pass

    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Return list of supported report formats.

        Returns:
            List of format names (e.g., ["html", "markdown", "json"])
        """
        pass
```

---

## Contract Tests

**Test Location**: `tests/contract/test_application_interfaces.py`

```python
import pytest
from fileorg.application.interfaces.ai_backend import IAIBackend, ClassificationRequest
from fileorg.application.interfaces.parser import IParserFactory, IParser
from fileorg.application.interfaces.report_generator import IReportGenerator
from fileorg.infrastructure.ai.local_backend import LocalBackend
from fileorg.infrastructure.parsers.factory import ParserFactory
from fileorg.infrastructure.reporters.generator import ReportGenerator

class TestApplicationInterfaceContracts:
    """Verify infrastructure implementations satisfy application interfaces."""

    # IAIBackend Tests
    def test_ai_backend_implements_interface(self):
        """All AI backends must implement IAIBackend."""
        backend = LocalBackend()
        assert isinstance(backend, IAIBackend)
        assert hasattr(backend, 'classify')
        assert hasattr(backend, 'health_check')
        assert hasattr(backend, 'backend_name')

    def test_classify_returns_valid_category_count(self):
        """classify() must return 5-15 categories."""
        backend = LocalBackend()
        request = ClassificationRequest(
            texts=["sample text"] * 20,
            max_categories=15
        )

        response = backend.classify(request)

        assert 5 <= len(response.categories) <= 15

    def test_classify_category_names_are_valid_folder_names(self):
        """Category names must be valid folder names."""
        backend = LocalBackend()
        request = ClassificationRequest(texts=["test"] * 10)

        response = backend.classify(request)

        for category in response.categories:
            # No special characters that are invalid in folder names
            assert not any(c in category.name for c in ['<', '>', ':', '"', '/', '\\', '|', '?', '*'])
            assert category.name.strip() == category.name  # No leading/trailing spaces

    def test_health_check_does_not_raise_exceptions(self):
        """health_check() must not raise exceptions."""
        backend = LocalBackend()
        # Should return bool, not raise
        result = backend.health_check()
        assert isinstance(result, bool)

    # IParserFactory Tests
    def test_parser_factory_implements_interface(self):
        """ParserFactory must implement IParserFactory."""
        factory = ParserFactory()
        assert isinstance(factory, IParserFactory)
        assert hasattr(factory, 'get_parser')
        assert hasattr(factory, 'register_parser')

    def test_get_parser_returns_none_for_unsupported(self, tmp_path):
        """get_parser() must return None for unsupported files."""
        factory = ParserFactory()
        unsupported_file = tmp_path / "test.xyz"  # Unsupported extension
        unsupported_file.touch()

        parser = factory.get_parser(unsupported_file)

        assert parser is None

    def test_parser_can_parse_completes_quickly(self, tmp_path):
        """can_parse() must complete in <10ms."""
        factory = ParserFactory()
        test_file = tmp_path / "test.pdf"
        test_file.write_text("content")

        import time
        start = time.time()
        parser = factory.get_parser(test_file)
        if parser:
            parser.can_parse(test_file)
        duration = time.time() - start

        assert duration < 0.010  # 10ms

    def test_parse_never_raises_exceptions(self, tmp_path):
        """parse() must never raise exceptions."""
        factory = ParserFactory()
        # Create a corrupted file
        corrupted = tmp_path / "corrupted.pdf"
        corrupted.write_bytes(b"NOT A REAL PDF")

        parser = factory.get_parser(corrupted)
        if parser:
            result = parser.parse(corrupted)  # Should not raise
            assert isinstance(result, ParseResult)
            # On error, success should be False
            if not result.success:
                assert result.error_message is not None

    # IReportGenerator Tests
    def test_report_generator_implements_interface(self):
        """ReportGenerator must implement IReportGenerator."""
        generator = ReportGenerator()
        assert isinstance(generator, IReportGenerator)
        assert hasattr(generator, 'generate')
        assert hasattr(generator, 'supported_formats')

    def test_generate_creates_output_dir(self, tmp_path):
        """generate() must create output directory if it doesn't exist."""
        generator = ReportGenerator()
        output_dir = tmp_path / "reports" / "nested"
        request = ReportRequest(
            result=mock_organization_result(),
            categories=[],
            output_dir=output_dir,
            formats=["html"]
        )

        response = generator.generate(request)

        assert output_dir.exists()
        assert response.success

    def test_generate_all_requested_formats(self, tmp_path):
        """generate() must create all requested formats."""
        generator = ReportGenerator()
        request = ReportRequest(
            result=mock_organization_result(),
            categories=[],
            output_dir=tmp_path,
            formats=["html", "markdown", "json"]
        )

        response = generator.generate(request)

        assert response.success
        assert len(response.reports) == 3
        formats = {r.format for r in response.reports}
        assert formats == {"html", "markdown", "json"}
```

---

## Implementation Examples

### LocalBackend Implementation

```python
# infrastructure/ai/local_backend.py
from transformers import pipeline
from fileorg.application.interfaces.ai_backend import (
    IAIBackend,
    ClassificationRequest,
    ClassificationResponse,
    CategoryPrediction
)

class LocalBackend(IAIBackend):
    """Local CPU/GPU AI backend using transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model = pipeline("zero-shot-classification", model=model_name)
        self._backend_name = f"Local CPU ({model_name})"

    def classify(self, request: ClassificationRequest) -> ClassificationResponse:
        """Implement classification using transformers."""
        import time
        start = time.time()

        # AI logic here...
        categories = self._perform_classification(request)

        processing_time = (time.time() - start) * 1000  # ms

        return ClassificationResponse(
            categories=categories,
            processing_time_ms=processing_time,
            model_name=self._backend_name
        )

    def health_check(self) -> bool:
        """Check if model is loaded."""
        try:
            return self._model is not None
        except Exception:
            return False

    @property
    def backend_name(self) -> str:
        return self._backend_name
```

---

## Version History

- **v1.0** (2025-10-19): Initial contract definition
