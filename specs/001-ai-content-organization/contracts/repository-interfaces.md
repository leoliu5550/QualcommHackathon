# Repository Interfaces Contract

**Feature**: DEV-docs/create-spec
**Date**: 2025-10-19
**Version**: 1.0

## Overview

This contract defines the repository interfaces that domain layer exposes and infrastructure layer implements. Repositories abstract all data access operations, allowing domain logic to remain independent of persistence mechanisms.

---

## Core Principles

1. **Repositories belong to the domain**: Interfaces defined in `domain/repositories/`, implementations in `infrastructure/persistence/`
2. **Domain language**: Methods use domain terminology, not persistence terminology (e.g., `get_organization()` not `query_db()`)
3. **No leaky abstractions**: Return types are domain models, never database/ORM objects
4. **Stateless**: Each method call is independent
5. **Error handling**: Raise domain exceptions, not infrastructure exceptions

---

## IFileRepository Interface

**Location**: `src/fileorg/domain/repositories/file_repository.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from ..models.file import FileMetadata

class IFileRepository(ABC):
    """File operations repository interface.

    This interface abstracts all file system interactions, allowing the domain
    layer to work with files without knowing about the underlying storage mechanism.
    """

    @abstractmethod
    def scan_folder(
        self,
        folder_path: Path,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[FileMetadata]:
        """Scan a folder and return metadata for all discoverable files.

        Args:
            folder_path: Absolute path to folder to scan
            exclude_patterns: Optional list of glob patterns to exclude
                            (e.g., [".git", "**/__pycache__"])

        Returns:
            List of FileMetadata for all accessible files

        Raises:
            FolderNotFoundError: If folder_path does not exist
            PermissionDeniedError: If folder_path is not readable

        Contract:
            - Must return empty list if folder is empty
            - Must skip files that cannot be read (no exception)
            - Must follow symlinks (configurable in implementation)
            - Must NOT include directories in results
        """
        pass

    @abstractmethod
    def read_file_content(self, file_path: Path) -> bytes:
        """Read raw file content.

        Args:
            file_path: Absolute path to file

        Returns:
            Raw file content as bytes

        Raises:
            FileNotFoundError: If file does not exist
            PermissionDeniedError: If file is not readable

        Contract:
            - Must return complete file content
            - Must handle large files (streaming in implementation)
        """
        pass

    @abstractmethod
    def move_file(self, source: Path, destination: Path) -> None:
        """Move file from source to destination.

        Args:
            source: Current file location (must exist)
            destination: Target location (parent folder must exist)

        Raises:
            FileNotFoundError: If source does not exist
            PermissionDeniedError: If insufficient permissions
            DestinationExistsError: If destination already exists

        Contract:
            - Must be atomic (rollback if fails)
            - Must preserve file attributes (timestamps, permissions)
            - Must NOT overwrite existing files
        """
        pass

    @abstractmethod
    def create_folder(self, folder_path: Path) -> None:
        """Create folder and all parent folders if needed.

        Args:
            folder_path: Path to folder to create

        Raises:
            PermissionDeniedError: If insufficient permissions

        Contract:
            - Must be idempotent (no error if folder exists)
            - Must create parent folders if needed
        """
        pass

    @abstractmethod
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file.

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal SHA-256 checksum

        Raises:
            FileNotFoundError: If file does not exist
            PermissionDeniedError: If file is not readable

        Contract:
            - Must use SHA-256 algorithm
            - Must handle large files efficiently (chunked reading)
            - Must return lowercase hex string
        """
        pass

    @abstractmethod
    def get_available_space(self, folder_path: Path) -> int:
        """Get available disk space in bytes.

        Args:
            folder_path: Path to check

        Returns:
            Available space in bytes

        Contract:
            - Must return accurate value within 1% margin
        """
        pass
```

---

## IBackupRepository Interface

**Location**: `src/fileorg/domain/repositories/backup_repository.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path
from ..models.backup import BackupManifest

class IBackupRepository(ABC):
    """Backup manifest persistence repository interface."""

    @abstractmethod
    def save(self, manifest: BackupManifest, path: Path) -> None:
        """Persist backup manifest to storage.

        Args:
            manifest: BackupManifest to save
            path: Target file path (typically .backup/file_paths.json)

        Raises:
            PermissionDeniedError: If cannot write to path

        Contract:
            - Must create parent directories if needed
            - Must be atomic (write to temp file, then rename)
            - Must validate manifest before saving
            - Format: JSON with pretty printing
        """
        pass

    @abstractmethod
    def load(self, path: Path) -> BackupManifest:
        """Load backup manifest from storage.

        Args:
            path: Path to backup manifest file

        Returns:
            Loaded BackupManifest

        Raises:
            FileNotFoundError: If manifest does not exist
            InvalidManifestError: If file is corrupted or invalid format

        Contract:
            - Must validate loaded data structure
            - Must convert string paths to Path objects
            - Must validate manifest version compatibility
        """
        pass

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Check if backup manifest exists.

        Args:
            path: Path to check

        Returns:
            True if manifest exists and is readable

        Contract:
            - Must return False if file exists but is not readable
            - Must NOT raise exceptions
        """
        pass

    @abstractmethod
    def delete(self, path: Path) -> None:
        """Delete backup manifest.

        Args:
            path: Path to manifest to delete

        Raises:
            PermissionDeniedError: If cannot delete file

        Contract:
            - Must be idempotent (no error if file doesn't exist)
        """
        pass
```

---

## Contract Tests

**Test Location**: `tests/contract/test_repository_contracts.py`

### Test: All repository implementations must satisfy interface

```python
import pytest
from fileorg.domain.repositories.file_repository import IFileRepository
from fileorg.domain.repositories.backup_repository import IBackupRepository
from fileorg.infrastructure.persistence.file_system_repository import FileSystemRepository
from fileorg.infrastructure.persistence.backup_repository_impl import BackupRepositoryImpl

class TestRepositoryContracts:
    """Verify all repository implementations satisfy their contracts."""

    def test_file_repository_implements_interface(self):
        """FileSystemRepository must implement IFileRepository."""
        repo = FileSystemRepository()
        assert isinstance(repo, IFileRepository)
        assert hasattr(repo, 'scan_folder')
        assert hasattr(repo, 'move_file')
        assert hasattr(repo, 'create_folder')
        assert hasattr(repo, 'calculate_checksum')
        assert hasattr(repo, 'get_available_space')

    def test_backup_repository_implements_interface(self):
        """BackupRepositoryImpl must implement IBackupRepository."""
        repo = BackupRepositoryImpl()
        assert isinstance(repo, IBackupRepository)
        assert hasattr(repo, 'save')
        assert hasattr(repo, 'load')
        assert hasattr(repo, 'exists')
        assert hasattr(repo, 'delete')

    def test_scan_folder_returns_file_metadata_list(self, tmp_path):
        """scan_folder must return List[FileMetadata]."""
        repo = FileSystemRepository()
        # Create test files
        (tmp_path / "test.txt").write_text("content")

        result = repo.scan_folder(tmp_path)

        assert isinstance(result, list)
        assert all(isinstance(item, FileMetadata) for item in result)

    def test_scan_folder_empty_on_empty_directory(self, tmp_path):
        """scan_folder must return empty list for empty folder."""
        repo = FileSystemRepository()
        result = repo.scan_folder(tmp_path)
        assert result == []

    def test_move_file_raises_on_destination_exists(self, tmp_path):
        """move_file must raise DestinationExistsError if destination exists."""
        repo = FileSystemRepository()
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("content")
        dest.write_text("existing")

        with pytest.raises(DestinationExistsError):
            repo.move_file(source, dest)

    def test_create_folder_is_idempotent(self, tmp_path):
        """create_folder must not fail if folder already exists."""
        repo = FileSystemRepository()
        folder = tmp_path / "test_folder"

        repo.create_folder(folder)  # First call
        repo.create_folder(folder)  # Should not raise

        assert folder.exists()

    def test_calculate_checksum_consistent(self, tmp_path):
        """calculate_checksum must return same value for same content."""
        repo = FileSystemRepository()
        file = tmp_path / "test.txt"
        file.write_text("test content")

        checksum1 = repo.calculate_checksum(file)
        checksum2 = repo.calculate_checksum(file)

        assert checksum1 == checksum2
        assert isinstance(checksum1, str)
        assert len(checksum1) == 64  # SHA-256 hex length

    def test_backup_save_load_roundtrip(self, tmp_path):
        """Backup manifest save/load must preserve data."""
        repo = BackupRepositoryImpl()
        manifest = BackupManifest(
            version="1.0",
            timestamp=datetime.now(),
            source_folder=tmp_path,
            records=[],
            session_id="test-123"
        )
        backup_path = tmp_path / "backup.json"

        repo.save(manifest, backup_path)
        loaded = repo.load(backup_path)

        assert loaded.version == manifest.version
        assert loaded.session_id == manifest.session_id
        assert loaded.source_folder == manifest.source_folder
```

---

## Implementation Guidelines

### 1. Error Handling

**Domain Exceptions** (raise these):
```python
# domain/exceptions/domain_exceptions.py
class DomainException(Exception):
    """Base for all domain exceptions."""
    pass

class FileNotFoundError(DomainException):
    """File does not exist."""
    pass

class PermissionDeniedError(DomainException):
    """Insufficient permissions."""
    pass

class DestinationExistsError(DomainException):
    """Destination file already exists."""
    pass

class InvalidManifestError(DomainException):
    """Backup manifest is invalid or corrupted."""
    pass
```

**Infrastructure Exception Mapping**:
```python
# infrastructure/persistence/file_system_repository.py
import os
from fileorg.domain.exceptions import PermissionDeniedError as DomainPermissionError

class FileSystemRepository(IFileRepository):
    def move_file(self, source: Path, destination: Path) -> None:
        try:
            shutil.move(str(source), str(destination))
        except PermissionError as e:
            # Map infrastructure exception to domain exception
            raise DomainPermissionError(f"Cannot move file: {e}") from e
```

### 2. Performance Considerations

- **Chunked Reading**: For `calculate_checksum()`, read files in chunks
- **Lazy Loading**: `scan_folder()` should not read file content
- **Caching**: Implementation may cache checksums (not part of interface)

### 3. Testing Strategies

**Use In-Memory Implementation for Fast Tests**:
```python
# tests/fakes/in_memory_file_repository.py
class InMemoryFileRepository(IFileRepository):
    """In-memory implementation for fast testing."""

    def __init__(self):
        self._files: Dict[Path, bytes] = {}

    def scan_folder(self, folder_path: Path, exclude_patterns=None):
        return [
            FileMetadata(path=p, ...)
            for p in self._files.keys()
            if p.parent == folder_path
        ]

    def move_file(self, source: Path, destination: Path):
        if destination in self._files:
            raise DestinationExistsError()
        self._files[destination] = self._files.pop(source)
```

---

## Version History

- **v1.0** (2025-10-19): Initial contract definition for Clean Architecture
