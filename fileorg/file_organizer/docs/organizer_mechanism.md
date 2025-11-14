# File Organizer Mechanism

## Overview

The File Organizer module executes actual file-moving operations based on LLM classification results. It integrates with the restoration-point system to ensure actions are traceable and reversible.

---

## Execution Flow

### 1. Standard Workflow

```
Receive ClassificationOutput (Task3)
    ↓
Validate inputs (path_mappings, target_dir, root_dir)
    ↓
[Optional] Create restoration point (Task4)
    ↓
For each file:
    - Check source exists
    - Create target directory if needed
    - Resolve filename conflicts
    - Move file (shutil.move)
    ↓
Update restoration point
    ↓
Return ExecutionResult
```

### 2. Restoration Point Integration

When `create_restoration_point=True`:

**Before execution**

- Build a RestorationPoint from ClassificationOutput
- Create a FileOperation entry for each mapping
- Save manifest to:
  `target_dir/restoration_{timestamp}.json`

**During execution**

- Track operation status: success / failed / skipped

**After execution**

- Reload manifest
- Update `executed`, `error`, and `new_path` (if conflict resolution changed it)
- Save updated manifest

---

## Path Construction

All paths follow Task4’s rules:

```
new_path = Path(target_dir).resolve() / new_relative_path
```

Example:
`target_dir = "C:/Organized"`
`new_relative_path = "Reports/report.pdf"`
→ `C:/Organized/Reports/report.pdf`

---

## Dry-Run Mode

### Purpose

Preview all file operations without modifying the file system. Useful for verifying classification results, checking conflicts, and validating folder structure.

### How to Use

**Option 1 — dry_run=True**

```python
result = use_case.organize_files(..., dry_run=True)
```

**Option 2 — preview_organization**

```python
result = use_case.preview_organization(...)
```

### Behavior

- **Does not** move files or create restoration points
- **Does not** create folders
- **Does** validate source existence
- All operations are returned as “success”
- Logs mark actions with `[DRY-RUN]`

---

## Conflict Handling

Triggered when the target filename already exists.

### Automatic Renaming (default)

Appends numeric suffixes:

```
report.pdf → report_1.pdf → report_2.pdf → ...
```

Manifest is updated to reflect the actual final path.

### Strict Mode (`handle_conflict=False`)

* Operation fails
* Error: `"Target file already exists"`

---

## Error Handling

| Scenario                         | Action | Status    | Message                                    |
| -------------------------------- | ------ | --------- | ------------------------------------------ |
| Source missing                   | Skip   | `skipped` | `"Source file not found"`                  |
| Cannot create directory          | Fail   | `failed`  | `"Failed to create target directory: ..."` |
| Name conflict (strict)           | Fail   | `failed`  | `"Target file already exists"`             |
| Permission error                 | Fail   | `failed`  | `"Move failed: ..."`                       |
| Restoration-point creation issue | Warn   | —         | Logged warning                             |

---

## ExecutionResult Structure

```python
@dataclass
class ExecutionResult:
    total_count
    success_count
    failed_count
    skipped_count
    operations: List[OperationStatus]
    restoration_manifest_path
    execution_time
```

---

## Usage Examples

### Basic

```python
result = use_case.organize_files(
    classification_output=output,
    target_dir="C:/Organized",
    root_dir="C:/Documents",
    dry_run=False,
    create_restoration_point=True
)
```

### Preview + Execute

```python
preview = use_case.preview_organization(...)
# Show operations...
result = use_case.organize_files(...)
```

---

## Integration with Task4 (Restoration)

### Restore

```python
result = restoration_use_case.restore_from_manifest(
    manifest_path=".../restoration_XXXX.json",
    verify_target=True
)
```

### Path Consistency Rules

1. All paths are absolute
2. Use `Path.resolve()`
3. New path composition matches Task4
4. Conflict-resolved paths are immediately written back to the manifest

---

## References

- File Organizer interfaces: `fileorg/file_organizer/ports.py`
- Local file implementation: `fileorg/file_organizer/adapters/local_file_organizer.py`
- Use case logic: `fileorg/file_organizer/application/file_organization_use_case.py`
- Restoration docs: `fileorg/restoration/docs/restoration_mechanism.md`