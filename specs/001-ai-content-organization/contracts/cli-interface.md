# CLI Interface Contract

**Feature**: 001-ai-content-organization
**Date**: 2025-10-18
**Version**: 1.0

## Overview

This contract defines the command-line interface for FileOrg. All CLI implementations must conform to this specification.

---

## Command Signature

### Basic Invocation

```bash
fileorg <folder_path> [options]
```

**Arguments**:
- `folder_path` (required): Absolute or relative path to folder to organize

**Options**:
- `--preview`: Run in preview mode (analyze but don't move files)
- `--restore`: Restore folder to original structure using backup data
- `--backend <name>`: Specify AI backend ("qualcomm" or "local")
- `--help`: Display help information
- `--version`: Display version information

---

## Contract Specifications

### C1: Basic Organization

**Command**:
```bash
fileorg /path/to/folder
```

**Preconditions**:
- Folder path exists and is readable
- User has write permissions in folder
- Sufficient disk space available

**Postconditions**:
- Files organized into semantic categories
- Backup manifest created at `/path/to/folder/.backup/file_paths.json`
- Reports generated in `/path/to/folder/.reports/`
- Exit code 0 on success

**Expected Output**:
```
Scanning folder: /path/to/folder
Found 127 files to process

Analyzing content... [###########         ] 68%

Organization complete! ✓
  Files processed: 127
  Files organized: 124
  Files skipped: 3
  Categories created: 5

Reports generated in: /path/to/folder/.reports/
Backup saved: /path/to/folder/.backup/file_paths.json

To undo: fileorg /path/to/folder --restore
```

**Error Cases**:
- Folder doesn't exist → Exit code 1, error message
- Permission denied → Exit code 1, error message
- Disk full → Exit code 1, error message with space requirement

---

### C2: Preview Mode

**Command**:
```bash
fileorg /path/to/folder --preview
```

**Preconditions**:
- Folder path exists and is readable

**Postconditions**:
- NO files moved from original locations
- Proposed backup manifest created
- Reports generated showing proposed structure
- Exit code 0 on success

**Expected Output**:
```
Preview Mode: No files will be moved

Scanning folder: /path/to/folder
Found 127 files to process

Analyzing content... [####################] 100%

Preview complete!
  Files analyzed: 127
  Proposed categories: 5

Proposed organization:
  • Financial_Documents (23 files)
  • Medical_Records (12 files)
  • Work_Projects (45 files)
  • Personal_Correspondence (34 files)
  • Technical_Documentation (13 files)

Preview reports: /path/to/folder/.reports/

To execute: fileorg /path/to/folder
```

**Contract Guarantee**: After preview mode, all files MUST remain in original locations.

---

### C3: Restore Mode

**Command**:
```bash
fileorg /path/to/folder --restore
```

**Preconditions**:
- Folder was previously organized by FileOrg
- Backup manifest exists at `/path/to/folder/.backup/file_paths.json`
- Backup manifest is valid and readable

**Postconditions**:
- All files returned to original locations
- Backup manifest marked as restored or deleted
- Exit code 0 on success

**Expected Output**:
```
Restoring folder: /path/to/folder

Loading backup data...
Found 124 files to restore

Restoring... [####################] 100%

Restore complete! ✓
  Files restored: 124
  Files not found: 0

Folder returned to original state.
```

**Error Cases**:
- No backup found → Exit code 1, error message "No backup found. This folder has not been organized."
- Backup corrupted → Exit code 1, error message with validation failure
- Files missing → Exit code 2, warning message, partial restore

**Contract Guarantee**: Restore MUST return folder to exact state before organization.

---

### C4: Backend Selection

**Command**:
```bash
fileorg /path/to/folder --backend qualcomm
fileorg /path/to/folder --backend local
```

**Preconditions**:
- Backend name is valid ("qualcomm" or "local")
- For "qualcomm": Qualcomm NPU available and API accessible
- For "local": PyTorch and transformers installed

**Postconditions**:
- Organization uses specified backend
- Performance appropriate for backend type
- Exit code 0 on success

**Error Cases**:
- Invalid backend name → Exit code 1, error listing valid backends
- Backend unavailable → Exit code 1, error suggesting fallback
- NPU API unreachable → Exit code 1, error suggesting "local" backend

---

### C5: Help Display

**Command**:
```bash
fileorg --help
```

**Preconditions**: None

**Postconditions**:
- Help text displayed to stdout
- Exit code 0

**Expected Output**:
```
FileOrg - AI-Powered File Organization

Usage: fileorg <folder> [options]

Arguments:
  folder                 Path to folder to organize

Options:
  --preview             Analyze and preview without moving files
  --restore             Restore folder to original structure
  --backend <name>      AI backend: qualcomm or local (default: qualcomm)
  --help                Show this help message
  --version             Show version information

Examples:
  fileorg ~/Downloads                    # Organize Downloads folder
  fileorg ~/Documents --preview          # Preview organization
  fileorg ~/Downloads --restore          # Undo organization
  fileorg ~/Downloads --backend local    # Use CPU/GPU backend

For more information: https://github.com/leoliu5550/QualcommHackathon
```

---

### C6: Version Display

**Command**:
```bash
fileorg --version
```

**Preconditions**: None

**Postconditions**:
- Version information displayed to stdout
- Exit code 0

**Expected Output**:
```
FileOrg version 1.0.0
Python 3.11.5
```

---

## Exit Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 0 | Success | Operation completed successfully |
| 1 | Error | General error (invalid input, permissions, etc.) |
| 2 | Partial Success | Some operations succeeded, some failed |
| 3 | User Cancelled | User interrupted operation (Ctrl+C) |
| 127 | Invalid Command | Unrecognized command or option |

---

## Progress Indicators

**Requirements**:
- Progress must be shown for operations exceeding 2 seconds
- Progress format: `[###########         ] 68%`
- Updates at least every 1 second
- Final completion indicator

**Contract**:
```python
def show_progress(current: int, total: int, description: str) -> None:
    """Display progress indicator to stdout.

    Args:
        current: Current progress count
        total: Total items to process
        description: Progress stage description
    """
```

---

## Error Message Format

**Contract**: All error messages MUST follow this format:

```
❌ Error: <Brief description>
   Reason: <What went wrong>
   Action: <How to fix>
```

**Example**:
```
❌ Error: Cannot organize folder
   Reason: Insufficient disk space (need 2.3 GB, have 1.1 GB)
   Action: Free up disk space or choose a different folder
```

---

## Environment Variables (Optional)

**FILEORG_BACKEND**:
- Values: "qualcomm", "local"
- Default: "qualcomm"
- Overridden by --backend flag

**FILEORG_LOG_LEVEL**:
- Values: "DEBUG", "INFO", "WARNING", "ERROR"
- Default: "INFO"
- Controls logging verbosity

---

## Standard Streams

**stdout**: Normal output, progress indicators, results
**stderr**: Error messages, warnings
**stdin**: Not used (no interactive prompts in CLI mode)

---

## Configuration File Support (Future)

**Not implemented in v1.0, but reserved for future**:
```
~/.fileorg/config.yaml
```

---

## Test Scenarios

### Test Case 1: Valid Organization
```bash
$ fileorg /tmp/test-folder
# Expected: Success, exit code 0, files organized
```

### Test Case 2: Preview Mode Doesn't Move Files
```bash
$ fileorg /tmp/test-folder --preview
$ ls -la /tmp/test-folder/*.pdf  # Files still in original location
# Expected: Success, exit code 0, files NOT moved
```

### Test Case 3: Restore Returns Original State
```bash
$ fileorg /tmp/test-folder
$ fileorg /tmp/test-folder --restore
$ ls -la /tmp/test-folder
# Expected: Folder identical to pre-organization state
```

### Test Case 4: Invalid Folder Path
```bash
$ fileorg /nonexistent/folder
# Expected: Error message, exit code 1
```

### Test Case 5: Permission Denied
```bash
$ fileorg /root/restricted-folder
# Expected: Permission error, exit code 1
```

### Test Case 6: Restore Without Backup
```bash
$ fileorg /tmp/never-organized --restore
# Expected: Error "No backup found", exit code 1
```

---

## Contract Testing

**Test Implementation Location**: `tests/contract/test_cli_interface.py`

**Required Tests**:
1. `test_cli_accepts_folder_path()`: Basic argument parsing
2. `test_preview_flag_prevents_file_movement()`: Preview mode guarantee
3. `test_restore_flag_reverses_organization()`: Restore guarantee
4. `test_invalid_folder_returns_error()`: Error handling
5. `test_help_flag_displays_usage()`: Help output
6. `test_version_flag_displays_version()`: Version output
7. `test_exit_codes_correct()`: All exit codes match spec

---

## CLI Contract Version History

- **v1.0** (2025-10-18): Initial contract definition
