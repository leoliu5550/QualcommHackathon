# Data Model: AI-Powered File Organization

**Feature**: 001-ai-content-organization
**Date**: 2025-10-18
**Status**: Complete

## Overview

This document defines the core data structures and entities for FileOrg's AI-powered file organization system. The model focuses on representing files, their content, categorization, and organization metadata.

---

## Core Entities

### 1. FileMetadata

Represents a discovered file with its system attributes.

**Attributes**:
- `path` (str): Absolute file path
- `name` (str): File name including extension
- `extension` (str): File extension (e.g., ".pdf", ".docx")
- `size_bytes` (int): File size in bytes
- `created_at` (datetime): File creation timestamp
- `modified_at` (datetime): Last modification timestamp
- `is_readable` (bool): Whether file has read permissions

**Validation Rules**:
- `path` must be absolute and exist on file system
- `size_bytes` must be non-negative
- `extension` must start with "." or be empty

**State Transitions**: Immutable after creation (represents snapshot at scan time)

**Example**:
```python
FileMetadata(
    path="/Users/name/Downloads/invoice.pdf",
    name="invoice.pdf",
    extension=".pdf",
    size_bytes=245760,
    created_at=datetime(2025, 1, 15, 14, 30),
    modified_at=datetime(2025, 1, 15, 14, 30),
    is_readable=True
)
```

---

### 2. FileContent

Represents extracted content from a file for AI analysis.

**Attributes**:
- `file_metadata` (FileMetadata): Reference to the file
- `content_text` (str): Extracted text content or summary
- `word_count` (int): Number of words in extracted content
- `extraction_status` (ExtractionStatus): Success, Failed, or Partial
- `extraction_error` (Optional[str]): Error message if extraction failed
- `parser_used` (str): Name of parser that extracted content (e.g., "PDFParser")

**Validation Rules**:
- `content_text` should be limited to 1000-2000 words for AI efficiency
- `word_count` must match actual content
- `extraction_error` required if status is Failed

**State Transitions**:
```
Created → Extracting → (Success | Failed | Partial)
```

**Relationships**:
- One-to-one with FileMetadata
- Referenced by Category for classification

**Example**:
```python
FileContent(
    file_metadata=FileMetadata(...),
    content_text="Invoice #12345\nDate: January 15, 2025\nAmount: $1,234.56\n...",
    word_count=87,
    extraction_status=ExtractionStatus.SUCCESS,
    extraction_error=None,
    parser_used="PDFParser"
)
```

---

### 3. Category

Represents a semantic grouping for files based on AI analysis.

**Attributes**:
- `name` (str): Human-readable category name (e.g., "Financial_Documents")
- `description` (Optional[str]): Brief description of category purpose
- `file_paths` (List[str]): Absolute paths of files belonging to this category
- `confidence_score` (float): Average AI confidence for files in category (0.0-1.0)
- `creation_timestamp` (datetime): When category was created

**Validation Rules**:
- `name` must be valid folder name (no special characters, underscores allowed)
- `name` should be 1-3 words maximum
- `file_paths` must all exist and be absolute paths
- `confidence_score` must be between 0.0 and 1.0

**State Transitions**:
```
Created → Populating → Finalized
```

**Relationships**:
- One-to-many with FileContent (category contains multiple files)
- Multiple files can belong to same category

**Example**:
```python
Category(
    name="Financial_Documents",
    description="Invoices, receipts, and financial records",
    file_paths=[
        "/Users/name/Downloads/invoice.pdf",
        "/Users/name/Downloads/receipt_jan.pdf",
        "/Users/name/Downloads/bill.docx"
    ],
    confidence_score=0.92,
    creation_timestamp=datetime(2025, 10, 18, 15, 45)
)
```

---

### 4. BackupRecord

Represents tracking data for restoration capability.

**Attributes**:
- `original_path` (str): Absolute path before organization
- `new_path` (str): Absolute path after organization
- `moved_at` (datetime): Timestamp when file was moved
- `file_size_bytes` (int): File size (for verification)
- `checksum` (Optional[str]): File hash for integrity verification

**Validation Rules**:
- Both paths must be absolute
- `original_path` must have existed before organization
- `new_path` must exist after organization
- `file_size_bytes` must match actual file size

**State Transitions**:
```
Created → Persisted → (Restored | Expired)
```

**Relationships**:
- One-to-one with FileMetadata
- Aggregated in BackupManifest

**Example**:
```python
BackupRecord(
    original_path="/Users/name/Downloads/invoice.pdf",
    new_path="/Users/name/Downloads/Financial_Documents/invoice.pdf",
    moved_at=datetime(2025, 10, 18, 15, 46, 30),
    file_size_bytes=245760,
    checksum="a3d5f7e9..."
)
```

---

### 5. BackupManifest

Represents complete backup data for an organization session.

**Attributes**:
- `version` (str): Backup format version (e.g., "1.0")
- `timestamp` (datetime): When organization occurred
- `source_folder` (str): Root folder that was organized
- `records` (List[BackupRecord]): All file movement records
- `total_files_moved` (int): Count of files moved
- `session_id` (str): Unique identifier for this organization session

**Validation Rules**:
- `version` must follow semantic versioning
- `records` cannot be empty (must have moved at least one file)
- `total_files_moved` must equal len(records)

**State Transitions**:
```
Created → Accumulating Records → Finalized → Persisted (JSON)
```

**Persistence**:
- Stored as `.backup/file_paths.json` in source folder
- JSON format for human readability

**Example**:
```python
BackupManifest(
    version="1.0",
    timestamp=datetime(2025, 10, 18, 15, 46, 0),
    source_folder="/Users/name/Downloads",
    records=[BackupRecord(...), BackupRecord(...), ...],
    total_files_moved=127,
    session_id="20251018-154600-abc123"
)
```

---

### 6. OrganizationResult

Represents the outcome of an organization operation.

**Attributes**:
- `files_processed` (int): Total files analyzed
- `files_moved` (int): Files successfully moved
- `files_skipped` (int): Files skipped due to errors
- `categories_created` (List[str]): Category names created
- `errors` (List[OrganizationError]): Errors encountered
- `duration_seconds` (float): Total processing time
- `preview_mode` (bool): Whether this was preview (no files moved)
- `backup_path` (Optional[str]): Path to backup manifest file

**Validation Rules**:
- `files_processed` = `files_moved` + `files_skipped`
- If `preview_mode` is True, `files_moved` must be 0
- `duration_seconds` must be positive

**State Transitions**:
```
Created → Processing → Completed (Success | PartialSuccess | Failed)
```

**Relationships**:
- References Categories (via category names)
- Contains OrganizationErrors

**Example**:
```python
OrganizationResult(
    files_processed=127,
    files_moved=124,
    files_skipped=3,
    categories_created=["Financial_Documents", "Medical_Records", "Work_Projects"],
    errors=[OrganizationError(...), ...],
    duration_seconds=178.5,
    preview_mode=False,
    backup_path="/Users/name/Downloads/.backup/file_paths.json"
)
```

---

### 7. OrganizationError

Represents an error encountered during organization.

**Attributes**:
- `file_path` (str): Path to file that caused error
- `error_type` (ErrorType): Category of error (ParseFailed, PermissionDenied, etc.)
- `error_message` (str): Human-readable error description
- `recovery_action` (str): Suggested user action to resolve
- `timestamp` (datetime): When error occurred

**Validation Rules**:
- `error_message` must be actionable (explain what happened + how to fix)
- `recovery_action` required for all error types

**Error Types** (enum):
- `PARSE_FAILED`: Could not extract content from file
- `PERMISSION_DENIED`: Insufficient permissions to read file
- `FILE_LOCKED`: File is open in another application
- `CORRUPTED`: File appears corrupted
- `PASSWORD_PROTECTED`: File requires password
- `UNSUPPORTED_FORMAT`: File format not supported

**Example**:
```python
OrganizationError(
    file_path="/Users/name/Downloads/locked.docx",
    error_type=ErrorType.FILE_LOCKED,
    error_message="Cannot read file 'locked.docx' - file is currently open",
    recovery_action="Close the file in other applications and retry organization",
    timestamp=datetime(2025, 10, 18, 15, 45, 12)
)
```

---

### 8. OrganizationReport

Represents documentation of organization execution.

**Attributes**:
- `report_id` (str): Unique identifier for report
- `execution_timestamp` (datetime): When organization occurred
- `total_files_processed` (int): Files analyzed
- `categories` (Dict[str, int]): Category name → file count mapping
- `errors_encountered` (int): Total errors
- `processing_duration` (float): Duration in seconds
- `html_tree_path` (Optional[str]): Path to HTML tree visualization
- `markdown_summary_path` (Optional[str]): Path to Markdown summary
- `statistics_path` (Optional[str]): Path to statistics file

**Validation Rules**:
- `report_id` must be unique per organization session
- At least one report file path must be present

**State Transitions**:
```
Created → Generating Artifacts → Finalized
```

**Report Artifacts**:
1. **HTML Tree** (`tree_structure.html`): Visual hierarchical folder structure
2. **Markdown Summary** (`organize_report.md`): Text-based summary with statistics
3. **Statistics** (`statistics.json`): Structured data for analysis

**Example**:
```python
OrganizationReport(
    report_id="20251018-154600-abc123",
    execution_timestamp=datetime(2025, 10, 18, 15, 46, 0),
    total_files_processed=127,
    categories={
        "Financial_Documents": 23,
        "Medical_Records": 12,
        "Work_Projects": 45,
        "Personal_Correspondence": 34,
        "Technical_Documentation": 13
    },
    errors_encountered=3,
    processing_duration=178.5,
    html_tree_path=".reports/tree_structure.html",
    markdown_summary_path=".reports/organize_report.md",
    statistics_path=".reports/statistics.json"
)
```

---

## Enums and Constants

### ExtractionStatus
```python
class ExtractionStatus(Enum):
    SUCCESS = "success"          # Content extracted successfully
    FAILED = "failed"            # Extraction completely failed
    PARTIAL = "partial"          # Some content extracted, but incomplete
```

### ErrorType
```python
class ErrorType(Enum):
    PARSE_FAILED = "parse_failed"
    PERMISSION_DENIED = "permission_denied"
    FILE_LOCKED = "file_locked"
    CORRUPTED = "corrupted"
    PASSWORD_PROTECTED = "password_protected"
    UNSUPPORTED_FORMAT = "unsupported_format"
    DISK_FULL = "disk_full"
    UNKNOWN = "unknown"
```

### System Constants
```python
# Content extraction limits
MAX_CONTENT_WORDS = 2000
MAX_CONTENT_CHARS = 10000

# File processing limits
MAX_FILES_PER_BATCH = 20
MAX_FILE_SIZE_MB = 100

# Performance targets
TARGET_FILES_PER_MINUTE = 100
TARGET_AI_INFERENCE_MS = 500

# System directories to exclude
EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".backup", ".reports"}
```

---

## Data Flow

### Organization Workflow Data Flow

```
1. File Discovery
   Input: folder_path (str)
   Output: List[FileMetadata]

2. Content Extraction
   Input: List[FileMetadata]
   Output: List[FileContent]

3. AI Classification
   Input: List[FileContent]
   Output: List[Category]

4. File Organization
   Input: List[FileMetadata], List[Category]
   Output: BackupManifest, OrganizationResult

5. Report Generation
   Input: OrganizationResult, List[Category]
   Output: OrganizationReport
```

### Preview Mode Data Flow

```
1-3. Same as organization workflow

4. Preview Generation (NO file movement)
   Input: List[FileMetadata], List[Category]
   Output: BackupManifest (proposed), OrganizationResult (preview=True)

5. Report Generation (showing proposed structure)
   Input: OrganizationResult, List[Category]
   Output: OrganizationReport
```

### Restore Workflow Data Flow

```
1. Load Backup
   Input: backup_manifest_path (str)
   Output: BackupManifest

2. Validate Backup
   Input: BackupManifest
   Output: ValidationResult

3. Reverse File Movements
   Input: BackupManifest
   Output: RestoreResult
```

---

## Entity Relationships

```
FileMetadata (1) ←→ (1) FileContent
    ↓
FileContent (*) → (1) Category
    ↓
Category (*) → (1) OrganizationResult
    ↓
FileMetadata (*) → (1) BackupRecord
    ↓
BackupRecord (*) → (1) BackupManifest
    ↓
OrganizationResult (1) → (1) OrganizationReport
    ↓
OrganizationResult (1) → (*) OrganizationError
```

---

## Persistence Strategy

### File System Storage

**Backup Data**:
- Location: `{source_folder}/.backup/file_paths.json`
- Format: JSON (BackupManifest serialized)
- Retention: Permanent (until user deletes or restores)

**Reports**:
- Location: `{source_folder}/.reports/`
- Formats: HTML, Markdown, JSON
- Retention: Permanent (user can delete manually)

**Error Logs**:
- Location: `{source_folder}/.backup/errors.log`
- Format: Plain text with timestamps
- Retention: Permanent (appended on each run)

### In-Memory Only

- FileMetadata (recreated on each scan)
- FileContent (discarded after classification)
- Categories (used during organization, then persisted in reports)

---

## Data Validation

### Critical Validations (Enforced)

1. **Path Validation**:
   - All file paths must be absolute
   - Paths must exist on file system (except for planned operations)
   - No path traversal vulnerabilities (e.g., `../../`)

2. **Size Constraints**:
   - File content limited to MAX_CONTENT_WORDS
   - Memory usage monitored during batch processing
   - Category names limited to 50 characters

3. **Integrity Checks**:
   - Backup checksums verified before restore
   - File sizes compared before/after moves
   - All moved files accounted for in backup manifest

### Non-Critical Validations (Warnings)

1. **Content Quality**:
   - Empty content warnings (but not errors)
   - Low confidence scores logged but not blocking
   - Unusual category names flagged for review

---

## Performance Considerations

### Memory Optimization

- **Lazy Loading**: FileContent generated on-demand, not all at once
- **Batch Processing**: Process files in chunks of 20 to limit memory
- **Content Truncation**: Limit extracted content to 2000 words max

### Storage Optimization

- **Backup Compression**: Consider gzip for large backup manifests (future enhancement)
- **Report Incremental Updates**: Don't regenerate full reports on partial changes
- **Log Rotation**: Implement log rotation for long-running usage (future enhancement)

---

## Data Model Complete ✅

All core entities defined with attributes, validation rules, state transitions, and relationships. Ready for contract definition and implementation.
