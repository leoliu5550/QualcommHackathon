# Organizer Module — Minimal Developer Guide

## Responsibilities

- **organize**: Move files into the directory structure suggested by the LLM
- **restore**: Fully restore files according to `.backup/file_paths.json`

**Use Case → depends on → IFileOrganizer (interface)**  
**IFileOrganizer → implemented by → LocalFileOrganizer**

---

# organize() — Core Flow

```
Input: ClassificationOutput + root_dir
1. Create .backup/
2. Create FilePathRecord (initial_path / original / new)
3. Move files (with conflict handling)
4. Write .backup/file_paths.json
5. Delete empty directories
Output: ExecutionResult
```

### Conflict Handling

```
file.pdf → file_1.pdf → file_2.pdf ...
```

### Directory Cleanup

Delete all empty directories (depth-first, from deepest to shallowest).

---

# restore() — Core Flow

```
Input: root_dir
1. Load .backup/file_paths.json
2. Locate files (original location / after manual moves)
3. Move back to initial_path (with conflict handling)
4. Remove empty directories created by the organization process
Output: dict(restored, errors)
```

---

# Backup Format

`.backup/file_paths.json`:

```json
{
  "timestamp": "...",
  "file_paths": [
    {
      "initial_path": "...",
      "original": "...",
      "new": "..."
    }
  ]
}
```

**initial_path** = permanent baseline (restore target)
**new** = location after re-organizing


# Required Data Structures

### ClassificationOutput (from llm_classifier)

```python
path_mappings: Dict[str, FileMapping]

# FileMapping:
# old_path: str              # absolute path
# new_relative_path: str     # relative to root_dir
# category / summary / reason
```

### ExecutionResult (returned by organize)

```
total_count
success_count
failed_count
skipped_count
operations: List[OperationStatus]
backup_dir
execution_time
```


# Use Case Integration

```python
organizer = LocalFileOrganizer()
use_case = FileOrganizerUseCase(organizer)

result = use_case.organize_files(
    classification_output=classification_output,
    root_dir="C:/Docs",
    dry_run=False,
)

restore_result = use_case.restore_files("C:/Docs")
```


# Key Rules

- All paths must use `Path.resolve()`
- Any single file failure must **not** interrupt the whole process
- restore must always be able to find the file (even if it was manually moved)
- new_relative_path is determined by the llm_classifier
- new = root_dir / new_relative_path