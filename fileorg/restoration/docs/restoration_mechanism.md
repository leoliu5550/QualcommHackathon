# Task5 Documentation – Restoration Mechanism

## Module Overview

**Path:** `fileorg/restoration/`
**Purpose:** Creates restore points before file-organization tasks, tracks file operations, and supports rollback.

## Architecture

```
fileorg/restoration/
├── ports.py                       # Interfaces and data contracts
├── adapters/
│   └── json_restoration_manager.py  # JSON persistence
├── application/
│   └── restoration_use_case.py      # Application logic
└── tests/
    ├── unit/
    └── integration/
```

## Core Dataclasses

### `RestorationPoint`

Represents a full restore snapshot for one file-organization run.

```python
@dataclass
class RestorationPoint:
    timestamp: str
    root_dir: str
    target_dir: str
    file_operations: List[FileOperation]
    metadata: Optional[Dict[str, Any]]
```

### `FileOperation`

Describes a single file move.

```python
@dataclass
class FileOperation:
    old_path: str
    new_path: str
    category: str
    executed: bool
    error: Optional[str]
```

## Usage

### 1. Create & Save a Restore Point

```python
manager = JsonRestorationManager()
use_case = RestorationUseCase(manager)

restoration_point = use_case.create_and_save_restoration_point(
    classification_output=classification_output,
    target_dir="C:/Users/user/Organized",
    root_dir="C:/Users/user/Documents",
    manifest_path="C:/restore_points/2025-11-13.json"
)
```

### 2. Run a Restore (Rollback)

```python
result = use_case.restore_files("C:/restore_points/2025-11-13.json")

print(result)
```

### 3. Query Restore Point Info

```python
info = use_case.get_restoration_point_info(
    "C:/restore_points/2025-11-13.json"
)
print(info)
```

## Manifest Format (JSON)

```json
{
  "timestamp": "2025-11-13T14:30:00",
  "root_dir": "C:/Users/user/Documents",
  "target_dir": "C:/Users/user/Organized",
  "file_operations": [
    {
      "old_path": "...",
      "new_path": "...",
      "category": "Financial Reports",
      "executed": true,
      "error": null
    }
  ],
  "metadata": {
    "total_files": 10,
    "processing_time_ms": 1500
  }
}
```

## Integration

### From Task3 → Task5

* Input: `ClassificationOutput.path_mappings`
* Converts `FileMapping` → `FileOperation`
* Builds paths using:
  `new_path = target_dir / new_relative_path`

### Task5 ↔ Task4

* Before moving files: Task4 creates the restore point.
* After execution: Task4 updates `executed` and resaves the manifest.

### Path Consistency

```python
new_path = Path(target_dir).resolve() / new_relative_path
```

## Key Design Notes

1. All paths are absolute.
2. `pathlib.Path` is used for cross-platform safety.
3. Only operations with `executed=True` are restored.
4. Restore continues even if some files fail.

## Test Coverage

* Dataclass behavior
* JSON serialization
* Path composition
* Restore point creation
* File restore flow with error handling
* Task3 ↔ Task5 integration
* Full pipeline simulation

## Running Tests

```bash
pytest fileorg/restoration/tests/ -v
pytest fileorg/restoration/tests/unit/ -v
pytest fileorg/restoration/tests/integration/ -v
```

## Notes

* Store manifests in `.fileorg/restore_points/`
* Timestamp (ISO 8601) uniquely identifies each restore point
* Task4 must update execution status for correct rollback
* Missing files don’t block restore-point creation

## API Reference

### `IRestorationManager`

```python
create_restoration_point(...)
save_restoration_point(...)
load_restoration_point(...)
restore(...)
validate_restoration_point(...)
```

### `RestorationUseCase`

```python
create_and_save_restoration_point(...)
restore_files(...)
validate_manifest(...)
get_restoration_point_info(...)
```

## Example Outputs

### Restore Result

```python
{
    "total": 10,
    "restored": 8,
    "failed": 1,
    "skipped": 1,
    "errors": ["Cannot restore C:/file.pdf: file not found"]
}
```

### Info Summary

```python
{
    "timestamp": "2025-11-13T14:30:00",
    "root_dir": "C:/Documents",
    "target_dir": "C:/Organized",
    "total_operations": 10,
    "executed_operations": 9,
    "categories": ["Financial Reports", "Personal Photos", "Work Documents"],
    "metadata": {"total_files": 10}
}
```