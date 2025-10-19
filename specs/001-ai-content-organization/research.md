# Clean Architecture in Python - Research Document

**Date:** 2025-10-19
**Purpose:** Research findings for implementing Clean Architecture in Python

---

## Table of Contents
1. [Clean Architecture Layers](#1-clean-architecture-layers)
2. [SOLID Principles in Python](#2-solid-principles-in-python)
3. [Dependency Injection in Python](#3-dependency-injection-in-python)
4. [Repository Pattern](#4-repository-pattern)
5. [Use Case Pattern](#5-use-case-pattern)
6. [Plugin Architecture](#6-plugin-architecture)

---

## 1. Clean Architecture Layers

### Decision
Implement a four-layer Clean Architecture with strict dependency rules pointing inward:
1. **Domain Layer** (Core/Entities)
2. **Application Layer** (Use Cases)
3. **Infrastructure Layer** (External Adapters)
4. **Interface Layer** (Controllers/Presenters)

### Rationale
- **Testability**: Inner layers can be tested without external dependencies
- **Independence**: Business logic is independent of frameworks, UI, databases
- **Maintainability**: Changes in outer layers don't affect inner layers
- **Flexibility**: Easy to swap implementations (e.g., different databases, APIs)

### Layer Responsibilities

#### 1.1 Domain Layer (Innermost)
**Contains:**
- Entities (business objects)
- Value Objects (immutable business data)
- Domain Services (domain logic not belonging to entities)
- Repository Interfaces (abstract definitions)
- Domain Events
- Aggregates
- Policies and Rules

**Rules:**
- NO dependencies on outer layers
- NO framework dependencies
- Only Python standard library
- Pure business logic

**Example Structure:**
```python
# domain/entities/document.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Document:
    """Domain entity representing a document."""
    id: str
    content: str
    title: str
    created_at: datetime
    modified_at: Optional[datetime] = None

    def update_content(self, new_content: str) -> None:
        """Update document content with business rule validation."""
        if not new_content or not new_content.strip():
            raise ValueError("Document content cannot be empty")
        self.content = new_content
        self.modified_at = datetime.now()

# domain/value_objects/file_path.py
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class FilePath:
    """Value object for file paths."""
    path: Path

    def __post_init__(self):
        if not isinstance(self.path, Path):
            object.__setattr__(self, 'path', Path(self.path))

    def exists(self) -> bool:
        return self.path.exists()

    def __str__(self) -> str:
        return str(self.path)
```

#### 1.2 Application Layer
**Contains:**
- Use Cases (application workflows)
- Application Services
- DTOs (Data Transfer Objects)
- Port Interfaces (abstract gateways)
- Command/Query handlers (CQRS)

**Rules:**
- Depends ONLY on Domain layer
- Orchestrates domain objects
- Implements application-specific business rules
- Framework-agnostic

**Example Structure:**
```python
# application/use_cases/parse_document.py
from abc import ABC, abstractmethod
from domain.entities.document import Document
from domain.value_objects.file_path import FilePath

class IDocumentParser(ABC):
    """Port interface for document parsing."""
    @abstractmethod
    def parse(self, file_path: FilePath) -> Document:
        pass

class IDocumentRepository(ABC):
    """Port interface for document persistence."""
    @abstractmethod
    def save(self, document: Document) -> None:
        pass

    @abstractmethod
    def get_by_id(self, doc_id: str) -> Document:
        pass

class ParseDocumentUseCase:
    """Use case for parsing and saving documents."""

    def __init__(
        self,
        parser: IDocumentParser,
        repository: IDocumentRepository
    ):
        self._parser = parser
        self._repository = repository

    def execute(self, file_path: FilePath) -> Document:
        """Execute the parse document use case."""
        # Parse document using injected parser
        document = self._parser.parse(file_path)

        # Apply business rules
        if not document.content:
            raise ValueError("Parsed document has no content")

        # Save using injected repository
        self._repository.save(document)

        return document
```

#### 1.3 Infrastructure Layer
**Contains:**
- Repository implementations
- External API clients
- Database adapters
- File system operations
- Framework-specific code
- Third-party library integrations

**Rules:**
- Implements interfaces defined in Application/Domain layers
- Can depend on Domain and Application layers
- Contains all external dependencies

**Example Structure:**
```python
# infrastructure/parsers/markdown_parser.py
from application.use_cases.parse_document import IDocumentParser
from domain.entities.document import Document
from domain.value_objects.file_path import FilePath
from datetime import datetime
import markdown

class MarkdownParser(IDocumentParser):
    """Concrete implementation of document parser for Markdown."""

    def parse(self, file_path: FilePath) -> Document:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.path.read_text(encoding='utf-8')

        return Document(
            id=str(file_path.path),
            content=content,
            title=file_path.path.stem,
            created_at=datetime.now()
        )

# infrastructure/repositories/file_document_repository.py
from application.use_cases.parse_document import IDocumentRepository
from domain.entities.document import Document
from pathlib import Path
import json

class FileDocumentRepository(IDocumentRepository):
    """File system implementation of document repository."""

    def __init__(self, storage_path: Path):
        self._storage_path = storage_path
        self._storage_path.mkdir(parents=True, exist_ok=True)

    def save(self, document: Document) -> None:
        file_path = self._storage_path / f"{document.id}.json"
        data = {
            'id': document.id,
            'content': document.content,
            'title': document.title,
            'created_at': document.created_at.isoformat(),
            'modified_at': document.modified_at.isoformat() if document.modified_at else None
        }
        file_path.write_text(json.dumps(data, indent=2))

    def get_by_id(self, doc_id: str) -> Document:
        file_path = self._storage_path / f"{doc_id}.json"
        if not file_path.exists():
            raise ValueError(f"Document not found: {doc_id}")

        data = json.loads(file_path.read_text())
        return Document(
            id=data['id'],
            content=data['content'],
            title=data['title'],
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at']) if data['modified_at'] else None
        )
```

#### 1.4 Interface Layer (Outermost)
**Contains:**
- CLI controllers
- Web API controllers
- GUI views
- Request/Response models
- Presenters/ViewModels

**Rules:**
- Depends on Application layer
- Handles user interaction
- Formats output for presentation
- Framework-specific (FastAPI, Flask, Typer, etc.)

**Example Structure:**
```python
# interface/cli/parse_command.py
import typer
from pathlib import Path
from application.use_cases.parse_document import ParseDocumentUseCase
from domain.value_objects.file_path import FilePath

app = typer.Typer()

@app.command()
def parse(
    file_path: Path = typer.Argument(..., help="Path to document to parse"),
    use_case: ParseDocumentUseCase = typer.Depends(get_parse_use_case)
):
    """Parse a document and save it."""
    try:
        document = use_case.execute(FilePath(file_path))
        typer.echo(f"Successfully parsed: {document.title}")
        typer.echo(f"Document ID: {document.id}")
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1)
```

### The Dependency Rule Visualization

```
┌─────────────────────────────────────────┐
│     Interface Layer (CLI, API, GUI)     │
│         - Controllers                   │
│         - Presenters                    │
└──────────────┬──────────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────────┐
│     Infrastructure Layer                │
│         - Repository Implementations    │
│         - Parser Implementations        │
│         - External APIs                 │
└──────────────┬──────────────────────────┘
               │ depends on & implements
               ▼
┌─────────────────────────────────────────┐
│     Application Layer (Use Cases)       │
│         - Use Cases                     │
│         - Port Interfaces (IRepository) │
│         - DTOs                          │
└──────────────┬──────────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────────┐
│     Domain Layer (Entities)             │
│         - Entities                      │
│         - Value Objects                 │
│         - Domain Services               │
└─────────────────────────────────────────┘
```

### Alternatives Considered

#### Alternative 1: Three-Layer Architecture
- **Rejected Reason**: Less separation of concerns, mixing application logic with domain logic
- Harder to test in isolation
- Less flexible for changing frameworks

#### Alternative 2: Hexagonal Architecture (Ports and Adapters)
- **Why Not Chosen**: Similar to Clean Architecture but less prescriptive about internal layers
- Clean Architecture provides clearer guidance on Domain vs Application layer separation
- Both can coexist; Clean Architecture can be viewed as a specific implementation of Hexagonal

#### Alternative 3: Traditional Layered Architecture
- **Rejected Reason**: Typically has dependencies pointing outward or bidirectional
- Domain layer ends up depending on data access layer
- Harder to test, less flexible

### Key Takeaways
1. **Dependencies point inward only** - outer layers depend on inner layers
2. **Domain layer has no dependencies** - pure business logic
3. **Application layer coordinates** - orchestrates domain objects via use cases
4. **Infrastructure implements abstractions** - implements interfaces defined in inner layers
5. **Interface layer adapts** - converts external requests to use case calls

---

## 2. SOLID Principles in Python

### Decision
Apply all five SOLID principles with Python-specific implementations using:
- Abstract Base Classes (ABC) for interfaces
- Type hints for better contracts
- Dataclasses for cleaner data objects
- Protocol types for duck typing when appropriate

### 2.1 Single Responsibility Principle (SRP)

**Principle:** A class should have only one reason to change.

**Rationale:**
- Improves maintainability
- Easier to test
- Reduces coupling
- Clear purpose for each class

**Bad Example (Violates SRP):**
```python
class DocumentProcessor:
    """This class does too many things!"""

    def read_file(self, file_path: str) -> str:
        """File I/O responsibility"""
        with open(file_path, 'r') as f:
            return f.read()

    def parse_markdown(self, content: str) -> dict:
        """Parsing responsibility"""
        # Parse markdown to dict
        return {'title': 'Example', 'content': content}

    def save_to_database(self, data: dict) -> None:
        """Database responsibility"""
        # Save to database
        pass

    def send_email_notification(self, recipient: str) -> None:
        """Email notification responsibility"""
        # Send email
        pass
```

**Good Example (Follows SRP):**
```python
from pathlib import Path
from abc import ABC, abstractmethod

class FileReader:
    """Single responsibility: reading files."""

    def read(self, file_path: Path) -> str:
        return file_path.read_text(encoding='utf-8')

class MarkdownParser:
    """Single responsibility: parsing markdown."""

    def parse(self, content: str) -> dict:
        # Parse markdown logic
        return {'title': 'Example', 'content': content}

class DocumentRepository:
    """Single responsibility: document persistence."""

    def save(self, data: dict) -> None:
        # Save to database logic
        pass

class EmailNotifier:
    """Single responsibility: sending notifications."""

    def notify(self, recipient: str, message: str) -> None:
        # Send email logic
        pass

class DocumentProcessingWorkflow:
    """Orchestrates the workflow - this is a use case!"""

    def __init__(
        self,
        reader: FileReader,
        parser: MarkdownParser,
        repository: DocumentRepository,
        notifier: EmailNotifier
    ):
        self._reader = reader
        self._parser = parser
        self._repository = repository
        self._notifier = notifier

    def process(self, file_path: Path, notify_email: str) -> None:
        content = self._reader.read(file_path)
        data = self._parser.parse(content)
        self._repository.save(data)
        self._notifier.notify(notify_email, f"Processed {data['title']}")
```

### 2.2 Open-Closed Principle (OCP)

**Principle:** Software entities should be open for extension but closed for modification.

**Rationale:**
- Add new functionality without changing existing code
- Reduces risk of breaking existing features
- Promotes use of abstractions

**Bad Example (Violates OCP):**
```python
class DocumentParser:
    def parse(self, file_path: str, file_type: str) -> dict:
        if file_type == 'markdown':
            # Parse markdown
            return {'type': 'markdown', 'content': '...'}
        elif file_type == 'html':
            # Parse HTML
            return {'type': 'html', 'content': '...'}
        elif file_type == 'pdf':
            # Parse PDF
            return {'type': 'pdf', 'content': '...'}
        # Adding new format requires modifying this class!
```

**Good Example (Follows OCP):**
```python
from abc import ABC, abstractmethod
from pathlib import Path

class DocumentParser(ABC):
    """Abstract base class for all parsers."""

    @abstractmethod
    def parse(self, file_path: Path) -> dict:
        """Parse document and return structured data."""
        pass

    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Check if this parser supports the file."""
        pass

class MarkdownParser(DocumentParser):
    """Parser for Markdown files."""

    def parse(self, file_path: Path) -> dict:
        content = file_path.read_text()
        # Parse markdown logic
        return {'type': 'markdown', 'content': content}

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix in ['.md', '.markdown']

class HTMLParser(DocumentParser):
    """Parser for HTML files."""

    def parse(self, file_path: Path) -> dict:
        content = file_path.read_text()
        # Parse HTML logic
        return {'type': 'html', 'content': content}

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix in ['.html', '.htm']

class PDFParser(DocumentParser):
    """Parser for PDF files."""

    def parse(self, file_path: Path) -> dict:
        # Parse PDF logic
        return {'type': 'pdf', 'content': '...'}

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix == '.pdf'

class ParserRegistry:
    """Registry pattern for parser selection."""

    def __init__(self):
        self._parsers: list[DocumentParser] = []

    def register(self, parser: DocumentParser) -> None:
        """Register a new parser (extension without modification)."""
        self._parsers.append(parser)

    def get_parser(self, file_path: Path) -> DocumentParser:
        """Get appropriate parser for file."""
        for parser in self._parsers:
            if parser.supports(file_path):
                return parser
        raise ValueError(f"No parser found for {file_path}")

# Usage - adding new parsers doesn't modify existing code
registry = ParserRegistry()
registry.register(MarkdownParser())
registry.register(HTMLParser())
registry.register(PDFParser())
# Easy to add new parser: registry.register(JSONParser())
```

### 2.3 Liskov Substitution Principle (LSP)

**Principle:** Subtypes must be substitutable for their base types without breaking the program.

**Rationale:**
- Ensures inheritance is used correctly
- Maintains behavioral consistency
- Prevents unexpected bugs from polymorphism

**Bad Example (Violates LSP):**
```python
from abc import ABC, abstractmethod

class Document(ABC):
    @abstractmethod
    def save(self, path: str) -> None:
        pass

    @abstractmethod
    def delete(self) -> None:
        pass

class EditableDocument(Document):
    def save(self, path: str) -> None:
        # Save document
        print(f"Saved to {path}")

    def delete(self) -> None:
        # Delete document
        print("Deleted")

class ReadOnlyDocument(Document):
    def save(self, path: str) -> None:
        # VIOLATION: raises exception instead of saving
        raise NotImplementedError("Read-only documents cannot be saved!")

    def delete(self) -> None:
        # VIOLATION: raises exception
        raise NotImplementedError("Read-only documents cannot be deleted!")

# This breaks LSP - cannot substitute ReadOnlyDocument for Document
def process_document(doc: Document) -> None:
    doc.save("output.txt")  # This will fail for ReadOnlyDocument!
```

**Good Example (Follows LSP):**
```python
from abc import ABC, abstractmethod
from typing import Optional

class Document(ABC):
    """Base class for all documents."""

    @abstractmethod
    def get_content(self) -> str:
        pass

class ReadableDocument(Document):
    """Documents that can be read."""

    def __init__(self, content: str):
        self._content = content

    def get_content(self) -> str:
        return self._content

class WritableDocument(ReadableDocument):
    """Documents that can be read AND written."""

    def save(self, path: str) -> None:
        with open(path, 'w') as f:
            f.write(self._content)

    def delete(self) -> None:
        # Delete logic
        pass

class ReadOnlyDocument(ReadableDocument):
    """Documents that are explicitly read-only."""

    def __init__(self, content: str):
        super().__init__(content)
        # No save or delete methods - doesn't pretend to be writable

# Now we can safely substitute
def display_document(doc: Document) -> None:
    """Works with any Document subclass."""
    print(doc.get_content())

def save_if_writable(doc: Document, path: str) -> None:
    """Type-safe checking for writable documents."""
    if isinstance(doc, WritableDocument):
        doc.save(path)
    else:
        print("Document is read-only")
```

**Alternative using Composition (often better than inheritance):**
```python
from dataclasses import dataclass
from typing import Protocol

class Readable(Protocol):
    """Protocol for readable objects."""
    def read(self) -> str: ...

class Writable(Protocol):
    """Protocol for writable objects."""
    def write(self, content: str) -> None: ...

@dataclass
class Document:
    """Document using composition."""
    content: str
    storage: Optional[Writable] = None

    def read(self) -> str:
        return self.content

    def write(self, new_content: str) -> None:
        if self.storage is None:
            raise ValueError("Document is read-only")
        self.storage.write(new_content)
```

### 2.4 Interface Segregation Principle (ISP)

**Principle:** Clients should not be forced to depend on interfaces they don't use.

**Rationale:**
- Smaller, focused interfaces
- Easier to implement
- Reduces coupling
- Better composability

**Bad Example (Violates ISP):**
```python
from abc import ABC, abstractmethod

class DocumentProcessor(ABC):
    """Fat interface - forces clients to implement everything."""

    @abstractmethod
    def read(self, path: str) -> str:
        pass

    @abstractmethod
    def write(self, path: str, content: str) -> None:
        pass

    @abstractmethod
    def parse(self, content: str) -> dict:
        pass

    @abstractmethod
    def validate(self, content: str) -> bool:
        pass

    @abstractmethod
    def compress(self, content: str) -> bytes:
        pass

    @abstractmethod
    def encrypt(self, content: str) -> str:
        pass

class SimpleTextReader(DocumentProcessor):
    """Only needs to read, but forced to implement everything!"""

    def read(self, path: str) -> str:
        with open(path, 'r') as f:
            return f.read()

    # Forced to implement methods it doesn't need
    def write(self, path: str, content: str) -> None:
        raise NotImplementedError("Not supported")

    def parse(self, content: str) -> dict:
        raise NotImplementedError("Not supported")

    def validate(self, content: str) -> bool:
        raise NotImplementedError("Not supported")

    def compress(self, content: str) -> bytes:
        raise NotImplementedError("Not supported")

    def encrypt(self, content: str) -> str:
        raise NotImplementedError("Not supported")
```

**Good Example (Follows ISP):**
```python
from abc import ABC, abstractmethod

# Split into smaller, focused interfaces
class Readable(ABC):
    @abstractmethod
    def read(self, path: str) -> str:
        pass

class Writable(ABC):
    @abstractmethod
    def write(self, path: str, content: str) -> None:
        pass

class Parsable(ABC):
    @abstractmethod
    def parse(self, content: str) -> dict:
        pass

class Validatable(ABC):
    @abstractmethod
    def validate(self, content: str) -> bool:
        pass

class Compressible(ABC):
    @abstractmethod
    def compress(self, content: str) -> bytes:
        pass

class Encryptable(ABC):
    @abstractmethod
    def encrypt(self, content: str) -> str:
        pass

# Now classes implement only what they need
class TextFileReader(Readable):
    """Only implements reading."""

    def read(self, path: str) -> str:
        with open(path, 'r') as f:
            return f.read()

class TextFileWriter(Writable):
    """Only implements writing."""

    def write(self, path: str, content: str) -> None:
        with open(path, 'w') as f:
            f.write(content)

class MarkdownParser(Parsable):
    """Only implements parsing."""

    def parse(self, content: str) -> dict:
        return {'content': content}

class SecureDocumentHandler(Readable, Writable, Encryptable):
    """Implements multiple interfaces as needed."""

    def read(self, path: str) -> str:
        with open(path, 'r') as f:
            encrypted = f.read()
        return self.decrypt(encrypted)

    def write(self, path: str, content: str) -> None:
        encrypted = self.encrypt(content)
        with open(path, 'w') as f:
            f.write(encrypted)

    def encrypt(self, content: str) -> str:
        # Encryption logic
        return f"encrypted_{content}"

    def decrypt(self, content: str) -> str:
        # Decryption logic
        return content.replace("encrypted_", "")

# Usage with dependency injection
class DocumentService:
    def __init__(
        self,
        reader: Readable,
        writer: Writable,
        parser: Parsable
    ):
        # Each dependency is minimal and focused
        self._reader = reader
        self._writer = writer
        self._parser = parser
```

### 2.5 Dependency Inversion Principle (DIP)

**Principle:**
- High-level modules should not depend on low-level modules. Both should depend on abstractions.
- Abstractions should not depend on details. Details should depend on abstractions.

**Rationale:**
- Decouples high-level logic from implementation details
- Enables testing with mocks
- Allows swapping implementations
- Core principle of Clean Architecture

**Bad Example (Violates DIP):**
```python
import sqlite3

class SQLiteDocumentRepository:
    """Low-level implementation detail."""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)

    def save(self, doc: dict) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO documents VALUES (?, ?)",
            (doc['id'], doc['content'])
        )
        self.conn.commit()

class DocumentService:
    """High-level module depends on low-level SQLite implementation."""

    def __init__(self):
        # VIOLATION: Directly depends on concrete implementation
        self._repository = SQLiteDocumentRepository("docs.db")

    def process_document(self, doc: dict) -> None:
        # Business logic
        self._repository.save(doc)
        # Cannot easily test or swap database!
```

**Good Example (Follows DIP):**
```python
from abc import ABC, abstractmethod
from typing import Protocol

# Abstraction (interface)
class DocumentRepository(ABC):
    """Abstract repository - high-level interface."""

    @abstractmethod
    def save(self, doc: dict) -> None:
        pass

    @abstractmethod
    def get(self, doc_id: str) -> dict:
        pass

# Low-level implementation depends on abstraction
class SQLiteDocumentRepository(DocumentRepository):
    """Concrete implementation of abstraction."""

    def __init__(self, db_path: str):
        import sqlite3
        self.conn = sqlite3.connect(db_path)

    def save(self, doc: dict) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO documents VALUES (?, ?)",
            (doc['id'], doc['content'])
        )
        self.conn.commit()

    def get(self, doc_id: str) -> dict:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return {'id': row[0], 'content': row[1]}

class InMemoryDocumentRepository(DocumentRepository):
    """Alternative implementation for testing."""

    def __init__(self):
        self._storage = {}

    def save(self, doc: dict) -> None:
        self._storage[doc['id']] = doc

    def get(self, doc_id: str) -> dict:
        return self._storage.get(doc_id)

# High-level module depends on abstraction
class DocumentService:
    """Business logic depends on abstraction, not implementation."""

    def __init__(self, repository: DocumentRepository):
        # Dependency injection - receives abstraction
        self._repository = repository

    def process_document(self, doc: dict) -> None:
        # Business logic
        self._repository.save(doc)
        # Easy to test with InMemoryDocumentRepository
        # Easy to swap to different database

# Composition root (dependency injection setup)
def create_production_service() -> DocumentService:
    repository = SQLiteDocumentRepository("docs.db")
    return DocumentService(repository)

def create_test_service() -> DocumentService:
    repository = InMemoryDocumentRepository()
    return DocumentService(repository)
```

**Using Python Protocols (Duck Typing):**
```python
from typing import Protocol

class RepositoryProtocol(Protocol):
    """Protocol instead of ABC - more Pythonic for duck typing."""

    def save(self, doc: dict) -> None: ...
    def get(self, doc_id: str) -> dict: ...

class DocumentService:
    """Accepts anything that looks like a repository."""

    def __init__(self, repository: RepositoryProtocol):
        self._repository = repository

    def process_document(self, doc: dict) -> None:
        self._repository.save(doc)

# Any class with save() and get() methods works!
# No need to inherit from a base class
```

### Summary of SOLID in Python

| Principle | Key Takeaway | Python Tools |
|-----------|-------------|--------------|
| SRP | One class, one responsibility | Small focused classes, composition |
| OCP | Extend without modifying | ABC, inheritance, strategy pattern |
| LSP | Subtypes are substitutable | Careful inheritance, protocols |
| ISP | Small, focused interfaces | Multiple small ABCs, protocols |
| DIP | Depend on abstractions | ABC, Protocol, dependency injection |

### Alternatives Considered

#### Alternative 1: Ignoring SOLID (procedural approach)
- **Rejected**: Hard to test, maintain, and extend
- Everything in large functions/modules
- Tight coupling

#### Alternative 2: Over-engineering with SOLID
- **Rejected**: Can lead to too many abstractions
- Balance is key - apply pragmatically
- Don't create interfaces for things that won't change

#### Alternative 3: Using only Protocols instead of ABC
- **Consideration**: More Pythonic, allows duck typing
- **When to use**: For third-party integrations, optional dependencies
- **When to use ABC**: For internal architecture, explicit contracts

---

## 3. Dependency Injection in Python

### Decision
Use the `dependency-injector` library for complex applications with Container-Provider architecture.

### Rationale

**Why `dependency-injector`:**
1. **Mature and Production-Ready**: Well-tested, actively maintained since 2015
2. **Performance**: Written in Cython for speed
3. **Comprehensive**: Supports multiple provider types (Factory, Singleton, etc.)
4. **Configuration**: Built-in support for YAML, JSON, environment variables
5. **Testing**: Easy to override dependencies for testing
6. **Type Safety**: Works well with type hints and IDEs
7. **Framework Integration**: Works with FastAPI, Flask, Django

### Implementation Approach

#### 3.1 Container-Provider Architecture

```python
# containers.py
from dependency_injector import containers, providers
from pathlib import Path

from application.use_cases.parse_document import ParseDocumentUseCase
from infrastructure.parsers.markdown_parser import MarkdownParser
from infrastructure.repositories.file_document_repository import FileDocumentRepository

class Container(containers.DeclarativeContainer):
    """Main dependency injection container."""

    # Configuration
    config = providers.Configuration()

    # Infrastructure
    document_repository = providers.Singleton(
        FileDocumentRepository,
        storage_path=config.storage.path
    )

    markdown_parser = providers.Factory(
        MarkdownParser
    )

    # Use Cases
    parse_document_use_case = providers.Factory(
        ParseDocumentUseCase,
        parser=markdown_parser,
        repository=document_repository
    )
```

#### 3.2 Configuration Management

```python
# config.yaml
storage:
  path: "./data/documents"

parsers:
  markdown:
    enabled: true
  html:
    enabled: false

# main.py
from dependency_injector.wiring import Provide, inject
from containers import Container

def main():
    container = Container()
    container.config.from_yaml('config.yaml')

    # Wire dependencies
    container.wire(modules=[__name__])

    # Use the container
    use_case = container.parse_document_use_case()
    result = use_case.execute(FilePath(Path("example.md")))

if __name__ == "__main__":
    main()
```

#### 3.3 Dependency Injection with @inject

```python
from dependency_injector.wiring import inject, Provide
from containers import Container
from application.use_cases.parse_document import ParseDocumentUseCase

@inject
def process_file(
    file_path: str,
    use_case: ParseDocumentUseCase = Provide[Container.parse_document_use_case]
):
    """Dependencies automatically injected."""
    result = use_case.execute(FilePath(Path(file_path)))
    print(f"Processed: {result.title}")
```

#### 3.4 Testing with Overrides

```python
# test_document_service.py
import pytest
from containers import Container
from infrastructure.repositories.file_document_repository import FileDocumentRepository

class InMemoryDocumentRepository:
    """Test double."""
    def __init__(self):
        self._storage = {}

    def save(self, document):
        self._storage[document.id] = document

    def get_by_id(self, doc_id):
        return self._storage.get(doc_id)

@pytest.fixture
def container():
    container = Container()
    # Override repository with test implementation
    container.document_repository.override(
        providers.Singleton(InMemoryDocumentRepository)
    )
    return container

def test_parse_document(container):
    use_case = container.parse_document_use_case()
    # Test with in-memory repository
    result = use_case.execute(FilePath(Path("test.md")))
    assert result is not None
```

#### 3.5 Multiple Environments

```python
# containers.py
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Different repository based on environment
    document_repository = providers.Selector(
        config.environment,
        development=providers.Singleton(InMemoryDocumentRepository),
        production=providers.Singleton(
            FileDocumentRepository,
            storage_path=config.storage.path
        ),
        testing=providers.Singleton(InMemoryDocumentRepository)
    )

# main.py
container = Container()
container.config.environment.from_env("APP_ENV", "development")
```

#### 3.6 Resource Management

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):

    # Resource with lifecycle management
    database_connection = providers.Resource(
        init_database_connection,
        connection_string=config.database.url
    )

    # Repository using the resource
    document_repository = providers.Factory(
        DatabaseDocumentRepository,
        connection=database_connection
    )

def init_database_connection(connection_string: str):
    """Resource initializer with cleanup."""
    conn = create_connection(connection_string)
    yield conn
    conn.close()  # Cleanup when container shuts down
```

### Alternatives Considered

#### Alternative 1: Manual Dependency Injection (Factory Pattern)

**Approach:**
```python
# factory.py
class ServiceFactory:
    @staticmethod
    def create_parse_use_case() -> ParseDocumentUseCase:
        repository = FileDocumentRepository(Path("./data"))
        parser = MarkdownParser()
        return ParseDocumentUseCase(parser, repository)

# Usage
use_case = ServiceFactory.create_parse_use_case()
```

**Pros:**
- Simple, no external dependencies
- Easy to understand
- Full control

**Cons:**
- Manual wiring of all dependencies
- No configuration management
- Harder to override for testing
- Doesn't scale well with many dependencies

**When to Use:** Small projects with few dependencies

#### Alternative 2: Python-Inject Library

**Approach:**
```python
import inject

def configure_dependencies(binder):
    binder.bind(DocumentRepository, FileDocumentRepository(Path("./data")))
    binder.bind(DocumentParser, MarkdownParser())

inject.configure(configure_dependencies)

class DocumentService:
    repository = inject.attr(DocumentRepository)
    parser = inject.attr(DocumentParser)
```

**Pros:**
- Simpler API than dependency-injector
- Automatic injection

**Cons:**
- Less feature-rich
- No built-in configuration management
- Less active maintenance
- Harder to test with overrides

**Why Not Chosen:** Less mature, fewer features, smaller community

#### Alternative 3: Constructor Injection Only (No Framework)

**Approach:**
```python
# Explicit dependency passing
class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        parser: DocumentParser
    ):
        self._repository = repository
        self._parser = parser

# Composition root in main.py
def create_app():
    repository = FileDocumentRepository(Path("./data"))
    parser = MarkdownParser()
    service = DocumentService(repository, parser)
    return service
```

**Pros:**
- Explicit and clear
- No magic
- Easy to understand

**Cons:**
- Manual composition root becomes complex
- No configuration management
- Repetitive for large applications

**When to Use:** Medium-sized projects, when you want full control

### Best Practices for Dependency Injection

1. **Program to Interfaces**: Always inject abstractions (ABC/Protocol), not concrete classes
2. **Constructor Injection**: Prefer constructor injection over property/setter injection
3. **Single Responsibility**: Containers should only handle dependency creation
4. **Configuration Separation**: Keep configuration separate from code (YAML/JSON files)
5. **Testing**: Use override mechanism for test doubles
6. **Avoid Service Locator**: Don't pass the container around; inject specific dependencies
7. **Lifecycle Management**: Choose appropriate provider (Singleton, Factory, etc.)

### Recommended Approach

**For Small Projects (< 10 dependencies):**
- Use manual dependency injection with factory pattern
- Keep it simple

**For Medium Projects (10-50 dependencies):**
- Use `dependency-injector` with basic Container
- Configuration from files

**For Large Projects (50+ dependencies):**
- Use `dependency-injector` with multiple containers
- Environment-specific configurations
- Resource management
- Integration with web frameworks

### Installation

```bash
pip install dependency-injector
```

---

## 4. Repository Pattern

### Decision
Implement Repository Pattern using Abstract Base Classes with separate repositories for different storage backends (file system, database, etc.).

### Rationale

**Why Repository Pattern:**
1. **Abstraction**: Separates domain from data access concerns
2. **Testability**: Easy to swap with in-memory implementation for tests
3. **Flexibility**: Switch storage backends without changing business logic
4. **Single Responsibility**: Centralizes data access logic
5. **Domain-Driven**: Collections of domain objects, not database tables

### 4.1 Core Repository Pattern

```python
# domain/repositories/document_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.document import Document

class IDocumentRepository(ABC):
    """Abstract repository interface in domain layer."""

    @abstractmethod
    def add(self, document: Document) -> None:
        """Add a new document to the repository."""
        pass

    @abstractmethod
    def get(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Document]:
        """Retrieve all documents."""
        pass

    @abstractmethod
    def update(self, document: Document) -> None:
        """Update an existing document."""
        pass

    @abstractmethod
    def delete(self, document_id: str) -> None:
        """Delete a document by ID."""
        pass

    @abstractmethod
    def find_by_title(self, title: str) -> List[Document]:
        """Find documents by title."""
        pass
```

### 4.2 File System Repository Implementation

```python
# infrastructure/repositories/file_system_document_repository.py
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

from domain.repositories.document_repository import IDocumentRepository
from domain.entities.document import Document

class FileSystemDocumentRepository(IDocumentRepository):
    """Repository implementation using file system storage."""

    def __init__(self, storage_path: Path):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._index_file = self._storage_path / "_index.json"
        self._ensure_index()

    def _ensure_index(self) -> None:
        """Ensure index file exists."""
        if not self._index_file.exists():
            self._index_file.write_text(json.dumps({}))

    def _read_index(self) -> dict:
        """Read the document index."""
        return json.loads(self._index_file.read_text())

    def _write_index(self, index: dict) -> None:
        """Write the document index."""
        self._index_file.write_text(json.dumps(index, indent=2))

    def _document_path(self, document_id: str) -> Path:
        """Get path for document file."""
        return self._storage_path / f"{document_id}.json"

    def _serialize_document(self, document: Document) -> dict:
        """Convert document to dictionary."""
        return {
            'id': document.id,
            'title': document.title,
            'content': document.content,
            'created_at': document.created_at.isoformat(),
            'modified_at': document.modified_at.isoformat() if document.modified_at else None
        }

    def _deserialize_document(self, data: dict) -> Document:
        """Convert dictionary to document."""
        return Document(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at']) if data['modified_at'] else None
        )

    def add(self, document: Document) -> None:
        """Add a new document."""
        # Check if document already exists
        if self._document_path(document.id).exists():
            raise ValueError(f"Document with id {document.id} already exists")

        # Save document file
        doc_data = self._serialize_document(document)
        self._document_path(document.id).write_text(json.dumps(doc_data, indent=2))

        # Update index
        index = self._read_index()
        index[document.id] = {
            'title': document.title,
            'created_at': document.created_at.isoformat()
        }
        self._write_index(index)

    def get(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by ID."""
        doc_path = self._document_path(document_id)
        if not doc_path.exists():
            return None

        data = json.loads(doc_path.read_text())
        return self._deserialize_document(data)

    def get_all(self) -> List[Document]:
        """Retrieve all documents."""
        index = self._read_index()
        documents = []

        for doc_id in index.keys():
            doc = self.get(doc_id)
            if doc:
                documents.append(doc)

        return documents

    def update(self, document: Document) -> None:
        """Update an existing document."""
        doc_path = self._document_path(document.id)
        if not doc_path.exists():
            raise ValueError(f"Document with id {document.id} not found")

        # Update document file
        doc_data = self._serialize_document(document)
        doc_path.write_text(json.dumps(doc_data, indent=2))

        # Update index
        index = self._read_index()
        index[document.id] = {
            'title': document.title,
            'created_at': index[document.id]['created_at']  # Keep original creation time
        }
        self._write_index(index)

    def delete(self, document_id: str) -> None:
        """Delete a document by ID."""
        doc_path = self._document_path(document_id)
        if not doc_path.exists():
            raise ValueError(f"Document with id {document_id} not found")

        # Delete document file
        doc_path.unlink()

        # Update index
        index = self._read_index()
        del index[document_id]
        self._write_index(index)

    def find_by_title(self, title: str) -> List[Document]:
        """Find documents by title (case-insensitive partial match)."""
        all_docs = self.get_all()
        return [
            doc for doc in all_docs
            if title.lower() in doc.title.lower()
        ]
```

### 4.3 In-Memory Repository (for Testing)

```python
# infrastructure/repositories/in_memory_document_repository.py
from typing import List, Optional, Dict

from domain.repositories.document_repository import IDocumentRepository
from domain.entities.document import Document

class InMemoryDocumentRepository(IDocumentRepository):
    """Repository implementation using in-memory storage (for testing)."""

    def __init__(self):
        self._storage: Dict[str, Document] = {}

    def add(self, document: Document) -> None:
        """Add a new document."""
        if document.id in self._storage:
            raise ValueError(f"Document with id {document.id} already exists")
        self._storage[document.id] = document

    def get(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by ID."""
        return self._storage.get(document_id)

    def get_all(self) -> List[Document]:
        """Retrieve all documents."""
        return list(self._storage.values())

    def update(self, document: Document) -> None:
        """Update an existing document."""
        if document.id not in self._storage:
            raise ValueError(f"Document with id {document.id} not found")
        self._storage[document.id] = document

    def delete(self, document_id: str) -> None:
        """Delete a document by ID."""
        if document_id not in self._storage:
            raise ValueError(f"Document with id {document_id} not found")
        del self._storage[document_id]

    def find_by_title(self, title: str) -> List[Document]:
        """Find documents by title."""
        return [
            doc for doc in self._storage.values()
            if title.lower() in doc.title.lower()
        ]

    def clear(self) -> None:
        """Clear all documents (useful for testing)."""
        self._storage.clear()
```

### 4.4 Database Repository Implementation (SQLAlchemy)

```python
# infrastructure/repositories/sqlalchemy_document_repository.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from domain.repositories.document_repository import IDocumentRepository
from domain.entities.document import Document
from infrastructure.database.models import DocumentModel

class SQLAlchemyDocumentRepository(IDocumentRepository):
    """Repository implementation using SQLAlchemy ORM."""

    def __init__(self, session: Session):
        self._session = session

    def _to_domain(self, model: DocumentModel) -> Document:
        """Convert ORM model to domain entity."""
        return Document(
            id=model.id,
            title=model.title,
            content=model.content,
            created_at=model.created_at,
            modified_at=model.modified_at
        )

    def _to_model(self, document: Document) -> DocumentModel:
        """Convert domain entity to ORM model."""
        return DocumentModel(
            id=document.id,
            title=document.title,
            content=document.content,
            created_at=document.created_at,
            modified_at=document.modified_at
        )

    def add(self, document: Document) -> None:
        """Add a new document."""
        model = self._to_model(document)
        self._session.add(model)
        self._session.commit()

    def get(self, document_id: str) -> Optional[Document]:
        """Retrieve a document by ID."""
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def get_all(self) -> List[Document]:
        """Retrieve all documents."""
        stmt = select(DocumentModel)
        models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(model) for model in models]

    def update(self, document: Document) -> None:
        """Update an existing document."""
        stmt = select(DocumentModel).where(DocumentModel.id == document.id)
        model = self._session.execute(stmt).scalar_one_or_none()

        if not model:
            raise ValueError(f"Document with id {document.id} not found")

        model.title = document.title
        model.content = document.content
        model.modified_at = document.modified_at

        self._session.commit()

    def delete(self, document_id: str) -> None:
        """Delete a document by ID."""
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        model = self._session.execute(stmt).scalar_one_or_none()

        if not model:
            raise ValueError(f"Document with id {document_id} not found")

        self._session.delete(model)
        self._session.commit()

    def find_by_title(self, title: str) -> List[Document]:
        """Find documents by title."""
        stmt = select(DocumentModel).where(DocumentModel.title.contains(title))
        models = self._session.execute(stmt).scalars().all()
        return [self._to_domain(model) for model in models]
```

### 4.5 Unit of Work Pattern (Advanced)

```python
# domain/repositories/unit_of_work.py
from abc import ABC, abstractmethod
from typing import Protocol

class IUnitOfWork(ABC):
    """Unit of Work pattern for transaction management."""

    @abstractmethod
    def __enter__(self):
        """Enter context manager."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit the transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the transaction."""
        pass

    @property
    @abstractmethod
    def documents(self) -> IDocumentRepository:
        """Get document repository."""
        pass

# infrastructure/repositories/file_system_unit_of_work.py
class FileSystemUnitOfWork(IUnitOfWork):
    """Unit of Work for file system operations."""

    def __init__(self, storage_path: Path):
        self._storage_path = storage_path
        self._documents_repo = None

    def __enter__(self):
        self._documents_repo = FileSystemDocumentRepository(self._storage_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        # File system commits are immediate
        pass

    def rollback(self) -> None:
        # Would need to implement transaction log for rollback
        pass

    @property
    def documents(self) -> IDocumentRepository:
        return self._documents_repo

# Usage in use case
class CreateDocumentUseCase:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    def execute(self, title: str, content: str) -> Document:
        with self._uow:
            document = Document(
                id=str(uuid.uuid4()),
                title=title,
                content=content,
                created_at=datetime.now()
            )
            self._uow.documents.add(document)
            self._uow.commit()
            return document
```

### Alternatives Considered

#### Alternative 1: Active Record Pattern
```python
class Document:
    def save(self):
        # Save itself to database
        pass

    @classmethod
    def find(cls, id):
        # Load from database
        pass
```

**Rejected Reason:**
- Mixes domain logic with persistence
- Hard to test
- Tight coupling to storage
- Violates SRP

#### Alternative 2: DAO (Data Access Object)
- Similar to Repository but more CRUD-focused
- Less domain-driven
- Repository is preferred in DDD/Clean Architecture

#### Alternative 3: Direct ORM Usage in Use Cases
- Violates dependency inversion
- Business logic couples to ORM
- Hard to test

### Best Practices

1. **Repository in Domain Layer**: Interface goes in domain, implementation in infrastructure
2. **Domain Objects**: Repository works with domain entities, not DTOs or database models
3. **Collection Abstraction**: Think of repository as a collection, not database
4. **Keep It Simple**: Don't add methods you don't need (YAGNI)
5. **Specification Pattern**: For complex queries, use Specification pattern
6. **One Repository Per Aggregate**: In DDD, one repository per aggregate root

---

## 5. Use Case Pattern

### Decision
Structure use cases as single-purpose classes with an `execute()` method that orchestrates domain services and repositories. Use cases belong in the Application layer.

### Rationale

**Why Use Case Pattern:**
1. **Single Responsibility**: Each use case handles one business workflow
2. **Testability**: Easy to test business workflows in isolation
3. **Clarity**: Explicit representation of application features
4. **Orchestration**: Coordinates domain services, repositories, and entities
5. **Decoupling**: Separates application logic from presentation layer

### 5.1 Basic Use Case Structure

```python
# application/use_cases/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')

class UseCase(ABC, Generic[TRequest, TResponse]):
    """Base class for all use cases."""

    @abstractmethod
    def execute(self, request: TRequest) -> TResponse:
        """Execute the use case."""
        pass
```

### 5.2 Simple Use Case Example

```python
# application/use_cases/create_document.py
from dataclasses import dataclass
from datetime import datetime
import uuid

from domain.entities.document import Document
from domain.repositories.document_repository import IDocumentRepository

@dataclass
class CreateDocumentRequest:
    """Input DTO for creating a document."""
    title: str
    content: str

@dataclass
class CreateDocumentResponse:
    """Output DTO for document creation."""
    document_id: str
    title: str
    created_at: datetime

class CreateDocumentUseCase:
    """Use case for creating a new document."""

    def __init__(self, repository: IDocumentRepository):
        self._repository = repository

    def execute(self, request: CreateDocumentRequest) -> CreateDocumentResponse:
        """Create a new document."""
        # Validate input
        if not request.title or not request.title.strip():
            raise ValueError("Title cannot be empty")

        if not request.content or not request.content.strip():
            raise ValueError("Content cannot be empty")

        # Create domain entity
        document = Document(
            id=str(uuid.uuid4()),
            title=request.title.strip(),
            content=request.content.strip(),
            created_at=datetime.now()
        )

        # Use repository
        self._repository.add(document)

        # Return response DTO
        return CreateDocumentResponse(
            document_id=document.id,
            title=document.title,
            created_at=document.created_at
        )
```

### 5.3 Complex Use Case with Domain Services

```python
# domain/services/document_parser_service.py
from abc import ABC, abstractmethod
from domain.entities.document import Document
from domain.value_objects.file_path import FilePath

class IDocumentParserService(ABC):
    """Domain service for parsing documents."""

    @abstractmethod
    def parse(self, file_path: FilePath) -> Document:
        """Parse a document from file."""
        pass

    @abstractmethod
    def supports_file(self, file_path: FilePath) -> bool:
        """Check if this parser supports the file type."""
        pass

# application/use_cases/import_document.py
from dataclasses import dataclass
from pathlib import Path
from typing import List

from domain.repositories.document_repository import IDocumentRepository
from domain.services.document_parser_service import IDocumentParserService
from domain.value_objects.file_path import FilePath

@dataclass
class ImportDocumentRequest:
    """Input DTO for importing a document."""
    file_path: Path

@dataclass
class ImportDocumentResponse:
    """Output DTO for document import."""
    document_id: str
    title: str
    success: bool
    message: str

class ImportDocumentUseCase:
    """Use case for importing documents from files."""

    def __init__(
        self,
        repository: IDocumentRepository,
        parsers: List[IDocumentParserService]
    ):
        self._repository = repository
        self._parsers = parsers

    def execute(self, request: ImportDocumentRequest) -> ImportDocumentResponse:
        """Import a document from a file."""
        file_path = FilePath(request.file_path)

        # Validate file exists
        if not file_path.exists():
            return ImportDocumentResponse(
                document_id="",
                title="",
                success=False,
                message=f"File not found: {file_path}"
            )

        # Find appropriate parser (domain service orchestration)
        parser = self._find_parser(file_path)
        if not parser:
            return ImportDocumentResponse(
                document_id="",
                title="",
                success=False,
                message=f"No parser found for file type: {file_path.path.suffix}"
            )

        try:
            # Parse document using domain service
            document = parser.parse(file_path)

            # Check for duplicates
            existing = self._repository.find_by_title(document.title)
            if existing:
                return ImportDocumentResponse(
                    document_id="",
                    title=document.title,
                    success=False,
                    message=f"Document with title '{document.title}' already exists"
                )

            # Save to repository
            self._repository.add(document)

            return ImportDocumentResponse(
                document_id=document.id,
                title=document.title,
                success=True,
                message="Document imported successfully"
            )

        except Exception as e:
            return ImportDocumentResponse(
                document_id="",
                title="",
                success=False,
                message=f"Error importing document: {str(e)}"
            )

    def _find_parser(self, file_path: FilePath) -> IDocumentParserService:
        """Find a parser that supports the file type."""
        for parser in self._parsers:
            if parser.supports_file(file_path):
                return parser
        return None
```

### 5.4 Use Case with Events (Advanced)

```python
# domain/events/document_created.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DocumentCreatedEvent:
    """Domain event raised when a document is created."""
    document_id: str
    title: str
    created_at: datetime

# domain/events/event_dispatcher.py
from abc import ABC, abstractmethod
from typing import List, Callable

class IEventDispatcher(ABC):
    """Interface for event dispatching."""

    @abstractmethod
    def dispatch(self, event) -> None:
        """Dispatch an event to all registered handlers."""
        pass

    @abstractmethod
    def register(self, event_type: type, handler: Callable) -> None:
        """Register an event handler."""
        pass

# application/use_cases/create_document_with_events.py
class CreateDocumentUseCase:
    """Use case with event dispatching."""

    def __init__(
        self,
        repository: IDocumentRepository,
        event_dispatcher: IEventDispatcher
    ):
        self._repository = repository
        self._event_dispatcher = event_dispatcher

    def execute(self, request: CreateDocumentRequest) -> CreateDocumentResponse:
        # Create document
        document = Document(
            id=str(uuid.uuid4()),
            title=request.title,
            content=request.content,
            created_at=datetime.now()
        )

        # Save to repository
        self._repository.add(document)

        # Dispatch domain event
        event = DocumentCreatedEvent(
            document_id=document.id,
            title=document.title,
            created_at=document.created_at
        )
        self._event_dispatcher.dispatch(event)

        return CreateDocumentResponse(
            document_id=document.id,
            title=document.title,
            created_at=document.created_at
        )
```

### 5.5 Preventing Use Case Bloat

From research, use cases tend to get bloated with:
- Business rules
- Validations
- Object creation
- Orchestration logic

**Solution: Push Complexity to Domain**

```python
# BAD: Fat use case
class CreateDocumentUseCase:
    def execute(self, request):
        # Validation logic (should be in domain)
        if not request.title:
            raise ValueError("Title required")
        if len(request.title) > 100:
            raise ValueError("Title too long")
        if not request.content:
            raise ValueError("Content required")

        # Business rules (should be in domain)
        if "forbidden" in request.content:
            raise ValueError("Content contains forbidden words")

        # Object creation (should be in factory)
        doc_id = str(uuid.uuid4())
        created_at = datetime.now()
        document = Document(doc_id, request.title, request.content, created_at)

        # Finally, the use case logic
        self._repository.add(document)

# GOOD: Thin use case with domain objects
class CreateDocumentUseCase:
    def __init__(
        self,
        repository: IDocumentRepository,
        factory: DocumentFactory,
        validator: DocumentValidator
    ):
        self._repository = repository
        self._factory = factory
        self._validator = validator

    def execute(self, request: CreateDocumentRequest) -> CreateDocumentResponse:
        # Validation in domain
        self._validator.validate_title(request.title)
        self._validator.validate_content(request.content)

        # Creation in factory
        document = self._factory.create_document(
            title=request.title,
            content=request.content
        )

        # Use case: orchestrate
        self._repository.add(document)

        return CreateDocumentResponse(
            document_id=document.id,
            title=document.title,
            created_at=document.created_at
        )
```

### 5.6 Testing Use Cases

```python
# tests/application/test_create_document_use_case.py
import pytest
from application.use_cases.create_document import (
    CreateDocumentUseCase,
    CreateDocumentRequest
)
from infrastructure.repositories.in_memory_document_repository import (
    InMemoryDocumentRepository
)

def test_create_document_success():
    # Arrange
    repository = InMemoryDocumentRepository()
    use_case = CreateDocumentUseCase(repository)
    request = CreateDocumentRequest(
        title="Test Document",
        content="This is test content"
    )

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.document_id is not None
    assert response.title == "Test Document"

    # Verify in repository
    saved_doc = repository.get(response.document_id)
    assert saved_doc is not None
    assert saved_doc.title == "Test Document"
    assert saved_doc.content == "This is test content"

def test_create_document_empty_title():
    # Arrange
    repository = InMemoryDocumentRepository()
    use_case = CreateDocumentUseCase(repository)
    request = CreateDocumentRequest(
        title="",
        content="Content"
    )

    # Act & Assert
    with pytest.raises(ValueError, match="Title cannot be empty"):
        use_case.execute(request)
```

### Alternatives Considered

#### Alternative 1: Service Layer
- Similar to use cases but often gets bloated
- Use cases are more focused and explicit

#### Alternative 2: Anemic Domain Model with Service Layer
- Domain objects are just data
- All logic in services
- **Rejected**: Violates OOP principles, loses domain richness

#### Alternative 3: Rich Domain Model Without Use Cases
- All logic in domain entities
- **Rejected**: Hard to orchestrate complex workflows, UI coupling

### Best Practices

1. **One Use Case = One Feature**: Each use case represents a single user action
2. **Thin Use Cases**: Push complexity to domain layer
3. **Input/Output DTOs**: Use request/response objects, not domain entities
4. **No UI Logic**: Use cases should be UI-agnostic
5. **Transaction Boundaries**: Use cases define transaction boundaries
6. **File Naming**: Name files by use case: `create_document.py`, `import_document.py`

---

## 6. Plugin Architecture

### Decision
Use Abstract Base Classes (ABC) with the `abc` module to create a plugin system for parsers and backends. Combine with a registry pattern for dynamic plugin discovery.

### Rationale

**Why ABC-Based Plugin Architecture:**
1. **Explicit Contracts**: Abstract methods ensure plugins implement required functionality
2. **Type Safety**: Works well with type checkers (mypy, pyright)
3. **Clear Intent**: Explicit is better than implicit (Zen of Python)
4. **Runtime Validation**: Raises errors if abstract methods not implemented
5. **IDE Support**: Better autocomplete and documentation
6. **Pythonic**: Standard library, no external dependencies

### 6.1 Basic Plugin Interface

```python
# domain/plugins/parser_plugin.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from domain.entities.document import Document
from domain.value_objects.file_path import FilePath

class ParserPlugin(ABC):
    """Abstract base class for document parser plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the parser name."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return list of supported file extensions (e.g., ['.md', '.markdown'])."""
        pass

    @abstractmethod
    def parse(self, file_path: FilePath) -> Document:
        """Parse a document from the given file path.

        Args:
            file_path: Path to the file to parse

        Returns:
            Parsed Document entity

        Raises:
            ValueError: If file cannot be parsed
            FileNotFoundError: If file doesn't exist
        """
        pass

    def supports_file(self, file_path: FilePath) -> bool:
        """Check if this parser supports the given file.

        Default implementation checks file extension.
        Override for custom logic.
        """
        return file_path.path.suffix.lower() in self.supported_extensions
```

### 6.2 Concrete Parser Plugin Implementations

```python
# infrastructure/plugins/parsers/markdown_parser_plugin.py
from datetime import datetime
from pathlib import Path
from typing import List
import uuid

from domain.plugins.parser_plugin import ParserPlugin
from domain.entities.document import Document
from domain.value_objects.file_path import FilePath

class MarkdownParserPlugin(ParserPlugin):
    """Parser plugin for Markdown files."""

    @property
    def name(self) -> str:
        return "Markdown Parser"

    @property
    def supported_extensions(self) -> List[str]:
        return ['.md', '.markdown', '.mdown']

    def parse(self, file_path: FilePath) -> Document:
        """Parse a Markdown file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.path.read_text(encoding='utf-8')

        # Extract title from first heading or filename
        title = self._extract_title(content, file_path.path)

        return Document(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            created_at=datetime.now()
        )

    def _extract_title(self, content: str, path: Path) -> str:
        """Extract title from content or use filename."""
        # Look for first # heading
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()

        # Fallback to filename
        return path.stem

# infrastructure/plugins/parsers/html_parser_plugin.py
from typing import List
from bs4 import BeautifulSoup
import uuid
from datetime import datetime

from domain.plugins.parser_plugin import ParserPlugin
from domain.entities.document import Document
from domain.value_objects.file_path import FilePath

class HTMLParserPlugin(ParserPlugin):
    """Parser plugin for HTML files."""

    @property
    def name(self) -> str:
        return "HTML Parser"

    @property
    def supported_extensions(self) -> List[str]:
        return ['.html', '.htm']

    def parse(self, file_path: FilePath) -> Document:
        """Parse an HTML file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.path.read_text(encoding='utf-8')
        soup = BeautifulSoup(content, 'html.parser')

        # Extract title from <title> tag or <h1>
        title = self._extract_title(soup, file_path.path)

        # Extract text content
        text_content = soup.get_text(separator='\n', strip=True)

        return Document(
            id=str(uuid.uuid4()),
            title=title,
            content=text_content,
            created_at=datetime.now()
        )

    def _extract_title(self, soup: BeautifulSoup, path: Path) -> str:
        """Extract title from HTML."""
        # Try <title> tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # Try first <h1>
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)

        # Fallback to filename
        return path.stem
```

### 6.3 Plugin Registry Pattern

```python
# application/plugins/parser_registry.py
from typing import Dict, List, Optional
from domain.plugins.parser_plugin import ParserPlugin
from domain.value_objects.file_path import FilePath

class ParserRegistry:
    """Registry for managing parser plugins."""

    def __init__(self):
        self._parsers: Dict[str, ParserPlugin] = {}

    def register(self, parser: ParserPlugin) -> None:
        """Register a parser plugin.

        Args:
            parser: Parser plugin to register

        Raises:
            ValueError: If parser with same name already registered
        """
        if parser.name in self._parsers:
            raise ValueError(f"Parser '{parser.name}' already registered")

        self._parsers[parser.name] = parser
        print(f"Registered parser: {parser.name} (supports: {parser.supported_extensions})")

    def unregister(self, parser_name: str) -> None:
        """Unregister a parser plugin by name."""
        if parser_name in self._parsers:
            del self._parsers[parser_name]

    def get_parser(self, file_path: FilePath) -> Optional[ParserPlugin]:
        """Get a parser that supports the given file.

        Args:
            file_path: File path to find parser for

        Returns:
            Parser plugin that supports the file, or None if not found
        """
        for parser in self._parsers.values():
            if parser.supports_file(file_path):
                return parser
        return None

    def get_parser_by_name(self, name: str) -> Optional[ParserPlugin]:
        """Get a parser by name."""
        return self._parsers.get(name)

    def list_parsers(self) -> List[ParserPlugin]:
        """Get list of all registered parsers."""
        return list(self._parsers.values())

    def list_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions."""
        extensions = set()
        for parser in self._parsers.values():
            extensions.update(parser.supported_extensions)
        return sorted(extensions)
```

### 6.4 Dynamic Plugin Discovery

```python
# application/plugins/plugin_loader.py
import importlib
import inspect
from pathlib import Path
from typing import List, Type
import sys

from domain.plugins.parser_plugin import ParserPlugin
from application.plugins.parser_registry import ParserRegistry

class PluginLoader:
    """Dynamically load plugins from a directory."""

    def __init__(self, registry: ParserRegistry):
        self._registry = registry

    def load_from_directory(self, plugin_dir: Path) -> int:
        """Load all parser plugins from a directory.

        Args:
            plugin_dir: Directory containing plugin modules

        Returns:
            Number of plugins loaded
        """
        if not plugin_dir.exists() or not plugin_dir.is_dir():
            raise ValueError(f"Plugin directory not found: {plugin_dir}")

        # Add directory to Python path
        sys.path.insert(0, str(plugin_dir.parent))

        loaded_count = 0

        # Find all Python files in directory
        for py_file in plugin_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue  # Skip __init__.py and private modules

            try:
                # Import the module
                module_name = f"{plugin_dir.name}.{py_file.stem}"
                module = importlib.import_module(module_name)

                # Find all ParserPlugin subclasses
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, ParserPlugin) and
                        obj is not ParserPlugin and
                        not inspect.isabstract(obj)):

                        # Instantiate and register
                        plugin_instance = obj()
                        self._registry.register(plugin_instance)
                        loaded_count += 1

            except Exception as e:
                print(f"Error loading plugin from {py_file}: {e}")

        return loaded_count

    def load_plugin_class(self, plugin_class: Type[ParserPlugin]) -> None:
        """Load a specific plugin class.

        Args:
            plugin_class: Plugin class to instantiate and register
        """
        if inspect.isabstract(plugin_class):
            raise ValueError(f"Cannot instantiate abstract class: {plugin_class}")

        if not issubclass(plugin_class, ParserPlugin):
            raise ValueError(f"Class must inherit from ParserPlugin: {plugin_class}")

        plugin_instance = plugin_class()
        self._registry.register(plugin_instance)
```

### 6.5 Backend Plugin Interface

```python
# domain/plugins/storage_backend_plugin.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class StorageBackendPlugin(ABC):
    """Abstract base class for storage backend plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the backend name."""
        pass

    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> None:
        """Connect to the storage backend.

        Args:
            config: Backend-specific configuration dictionary
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the storage backend."""
        pass

    @abstractmethod
    def save(self, key: str, data: bytes) -> None:
        """Save data to the backend.

        Args:
            key: Unique identifier for the data
            data: Binary data to save
        """
        pass

    @abstractmethod
    def load(self, key: str) -> bytes:
        """Load data from the backend.

        Args:
            key: Unique identifier for the data

        Returns:
            Binary data

        Raises:
            KeyError: If key not found
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete data from the backend.

        Args:
            key: Unique identifier for the data
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in backend.

        Args:
            key: Unique identifier to check

        Returns:
            True if key exists, False otherwise
        """
        pass

# infrastructure/plugins/backends/file_system_backend.py
from pathlib import Path
from typing import Any, Dict

from domain.plugins.storage_backend_plugin import StorageBackendPlugin

class FileSystemBackend(StorageBackendPlugin):
    """File system storage backend plugin."""

    def __init__(self):
        self._storage_path: Optional[Path] = None

    @property
    def name(self) -> str:
        return "File System Backend"

    def connect(self, config: Dict[str, Any]) -> None:
        """Connect to file system storage."""
        storage_path = config.get('path')
        if not storage_path:
            raise ValueError("Config must include 'path' key")

        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)

    def disconnect(self) -> None:
        """Disconnect (no-op for file system)."""
        self._storage_path = None

    def save(self, key: str, data: bytes) -> None:
        """Save data to a file."""
        if not self._storage_path:
            raise RuntimeError("Backend not connected")

        file_path = self._storage_path / key
        file_path.write_bytes(data)

    def load(self, key: str) -> bytes:
        """Load data from a file."""
        if not self._storage_path:
            raise RuntimeError("Backend not connected")

        file_path = self._storage_path / key
        if not file_path.exists():
            raise KeyError(f"Key not found: {key}")

        return file_path.read_bytes()

    def delete(self, key: str) -> None:
        """Delete a file."""
        if not self._storage_path:
            raise RuntimeError("Backend not connected")

        file_path = self._storage_path / key
        if file_path.exists():
            file_path.unlink()

    def exists(self, key: str) -> bool:
        """Check if file exists."""
        if not self._storage_path:
            raise RuntimeError("Backend not connected")

        file_path = self._storage_path / key
        return file_path.exists()
```

### 6.6 Usage Example

```python
# main.py
from pathlib import Path
from application.plugins.parser_registry import ParserRegistry
from application.plugins.plugin_loader import PluginLoader
from infrastructure.plugins.parsers.markdown_parser_plugin import MarkdownParserPlugin
from infrastructure.plugins.parsers.html_parser_plugin import HTMLParserPlugin
from domain.value_objects.file_path import FilePath

def main():
    # Create registry
    registry = ParserRegistry()

    # Option 1: Manual registration
    registry.register(MarkdownParserPlugin())
    registry.register(HTMLParserPlugin())

    # Option 2: Dynamic loading from directory
    # loader = PluginLoader(registry)
    # loaded = loader.load_from_directory(Path("./plugins/parsers"))
    # print(f"Loaded {loaded} plugins")

    # List registered parsers
    print("Registered parsers:")
    for parser in registry.list_parsers():
        print(f"  - {parser.name}: {parser.supported_extensions}")

    # Use a parser
    file_to_parse = FilePath(Path("example.md"))
    parser = registry.get_parser(file_to_parse)

    if parser:
        print(f"\nUsing {parser.name} to parse {file_to_parse}")
        document = parser.parse(file_to_parse)
        print(f"Parsed document: {document.title}")
    else:
        print(f"No parser found for {file_to_parse}")

if __name__ == "__main__":
    main()
```

### 6.7 Testing Plugins

```python
# tests/plugins/test_markdown_parser_plugin.py
import pytest
from pathlib import Path
from domain.value_objects.file_path import FilePath
from infrastructure.plugins.parsers.markdown_parser_plugin import MarkdownParserPlugin

def test_markdown_parser_name():
    parser = MarkdownParserPlugin()
    assert parser.name == "Markdown Parser"

def test_markdown_parser_supported_extensions():
    parser = MarkdownParserPlugin()
    assert '.md' in parser.supported_extensions
    assert '.markdown' in parser.supported_extensions

def test_markdown_parser_supports_file():
    parser = MarkdownParserPlugin()
    assert parser.supports_file(FilePath(Path("test.md")))
    assert parser.supports_file(FilePath(Path("test.markdown")))
    assert not parser.supports_file(FilePath(Path("test.html")))

def test_markdown_parser_parse(tmp_path):
    # Create a temporary markdown file
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test Title\n\nTest content")

    parser = MarkdownParserPlugin()
    document = parser.parse(FilePath(md_file))

    assert document.title == "Test Title"
    assert "Test content" in document.content

def test_markdown_parser_file_not_found():
    parser = MarkdownParserPlugin()
    with pytest.raises(FileNotFoundError):
        parser.parse(FilePath(Path("nonexistent.md")))
```

### Alternatives Considered

#### Alternative 1: Entry Points (setuptools)
```python
# setup.py
setup(
    entry_points={
        'my_app.parsers': [
            'markdown = my_plugins:MarkdownParser',
        ]
    }
)
```

**Pros:**
- Standard Python packaging approach
- Plugins can be separate packages

**Cons:**
- Requires package installation
- More complex setup
- Overkill for internal plugins

**When to Use:** For plugins distributed as separate packages

#### Alternative 2: Metaclass-based Registration
```python
class PluginMeta(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.plugins.append(cls)

class ParserPlugin(metaclass=PluginMeta):
    pass
```

**Pros:**
- Automatic registration

**Cons:**
- Implicit, less clear
- Harder to understand
- Less control over registration

**Why Not Chosen:** Too much magic, less explicit

#### Alternative 3: Decorator-based Registration
```python
parsers = []

def register_parser(cls):
    parsers.append(cls)
    return cls

@register_parser
class MarkdownParser:
    pass
```

**Pros:**
- Simple
- Explicit registration

**Cons:**
- Global state
- Hard to test
- No validation

**Why Not Chosen:** ABC provides better validation and contract enforcement

### Best Practices

1. **Use ABC for Contracts**: Abstract base classes enforce plugin interface
2. **Registry Pattern**: Centralize plugin management
3. **Validation**: Validate plugins on registration
4. **Documentation**: Document plugin interface clearly
5. **Error Handling**: Graceful handling of plugin failures
6. **Testing**: Test plugins in isolation
7. **Configuration**: Allow plugin configuration via dependency injection
8. **Versioning**: Consider plugin versioning for compatibility

### Summary

The ABC-based plugin architecture provides:
- **Clear contracts** with abstract methods
- **Type safety** with Python type hints
- **Runtime validation** of plugin implementation
- **Flexibility** for adding new plugins without modifying core code
- **Testability** through interface-based mocking
- **Discoverability** via registry and loader patterns

---

## Summary and Recommendations

### Technology Stack
- **Python**: 3.11+ (as per CLAUDE.md)
- **Dependency Injection**: `dependency-injector` library
- **Testing**: `pytest` for unit tests
- **Type Checking**: `mypy` or `pyright` for static type analysis

### Project Structure Recommendation

```
qualcomm-hackathon/
├── src/
│   ├── domain/                      # Domain Layer (no dependencies)
│   │   ├── entities/
│   │   │   └── document.py
│   │   ├── value_objects/
│   │   │   └── file_path.py
│   │   ├── repositories/
│   │   │   └── document_repository.py  # Interface only
│   │   ├── services/
│   │   │   └── document_parser_service.py  # Interface only
│   │   ├── events/
│   │   │   └── document_created.py
│   │   └── plugins/
│   │       ├── parser_plugin.py
│   │       └── storage_backend_plugin.py
│   │
│   ├── application/                 # Application Layer (depends on domain)
│   │   ├── use_cases/
│   │   │   ├── create_document.py
│   │   │   ├── import_document.py
│   │   │   └── parse_document.py
│   │   ├── plugins/
│   │   │   ├── parser_registry.py
│   │   │   └── plugin_loader.py
│   │   └── dtos/
│   │       └── document_dto.py
│   │
│   ├── infrastructure/              # Infrastructure Layer (depends on app+domain)
│   │   ├── repositories/
│   │   │   ├── file_system_document_repository.py
│   │   │   ├── in_memory_document_repository.py
│   │   │   └── sqlalchemy_document_repository.py
│   │   ├── plugins/
│   │   │   ├── parsers/
│   │   │   │   ├── markdown_parser_plugin.py
│   │   │   │   └── html_parser_plugin.py
│   │   │   └── backends/
│   │   │       └── file_system_backend.py
│   │   └── database/
│   │       └── models.py
│   │
│   ├── interface/                   # Interface Layer (depends on app)
│   │   ├── cli/
│   │   │   └── commands.py
│   │   └── api/
│   │       └── routes.py
│   │
│   └── containers.py                # DI Container
│
├── tests/                           # Tests mirror src/ structure
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interface/
│
└── config/
    ├── development.yaml
    ├── production.yaml
    └── test.yaml
```

### Implementation Checklist

- [ ] Set up domain layer with entities and value objects
- [ ] Define repository interfaces in domain layer
- [ ] Implement use cases in application layer
- [ ] Create repository implementations in infrastructure layer
- [ ] Set up dependency injection container
- [ ] Implement parser plugin system
- [ ] Create concrete parser plugins (Markdown, HTML, etc.)
- [ ] Set up CLI interface with Typer
- [ ] Write unit tests for all layers
- [ ] Configure different environments (dev, test, prod)
- [ ] Document plugin development guide

### Key Principles to Remember

1. **Dependencies point inward**: Outer layers depend on inner layers, never the reverse
2. **Domain is independent**: No framework or infrastructure dependencies
3. **Use abstractions**: Program to interfaces, not implementations
4. **Inject dependencies**: Use dependency injection for all cross-layer dependencies
5. **One responsibility**: Each class/module has one clear purpose
6. **Test in isolation**: Use interfaces and DI to enable unit testing

---

**Document Version**: 1.0
**Last Updated**: 2025-10-19
**Status**: Research Complete - Ready for Implementation
