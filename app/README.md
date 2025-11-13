# AI File Organizer – Quick Start Guide

This tool automatically organizes your files based on their types.


## 🚀 Quick Start

### 1. Preview the organization (no files will be moved)

```bash
python -m app.organizer "source_folder" "target_folder"
```

**Example:**

```bash
python -m app.organizer "C:/Users/user/Downloads" "C:/Users/user/Organized"
```

This shows how files *would* be organized, without actually moving them.

---

### 2. Run the organizer (files will be moved)

After reviewing the preview, add `--execute` to start:

```bash
python -m app.organizer "source_folder" "target_folder" --execute
```

**Example:**

```bash
python -m app.organizer "C:/Users/user/Downloads" "C:/Users/user/Organized" --execute
```

This will:

* ✅ Move files into categorized folders
* ✅ Automatically create a restoration point (for undo)
* ✅ Show summary statistics

---

## 🔄 Restoration

### Restore a single operation

If you're not satisfied with the result:

```bash
python -m app.organizer restore "path_to_restoration_file"
```

**Example:**

```bash
python -m app.organizer restore "C:/Users/user/Organized/restoration_20250113_143000.json"
```

Restoration files are created automatically after each run.

### Restore the entire batch

Yes — you can restore all files from that cleanup:

```bash
python -m app.organizer restore "C:/Organized/restoration_20250113_143000.json"
```

Each restoration file represents one complete cleanup session.

---

## 📂 File Categorization Rules

Current version uses simple extension-based grouping:

| File Types                      | Folder           |
| ------------------------------- | ---------------- |
| `.pdf`, `.doc`, `.docx`, `.txt` | `Documents/`     |
| `.xlsx`, `.xls`, `.csv`         | `Spreadsheets/`  |
| `.jpg`, `.png`, `.gif`          | `Images/`        |
| `.py`, `.js`, `.ts`, `.java`    | `Code/`          |
| `.zip`, `.rar`, `.7z`           | `Archives/`      |
| Others                          | `Miscellaneous/` |

---

## 📋 Full Example Workflow

```bash
# Step 1: Preview
python -m app.organizer "C:/Downloads" "C:/Organized"

# Step 2: Execute
python -m app.organizer "C:/Downloads" "C:/Organized" --execute

# Output:
# ============================================================
# Total: 25
# Success: 23
# Failed: 0
# Skipped: 2
# Restoration manifest: C:/Organized/restoration_20250113_143000.json
# ============================================================

# Step 3: Restore if needed
python -m app.organizer restore "C:/Organized/restoration_20250113_143000.json"

# All files return to their original places!
```

---

## ⚠️ Notes

1. **Preview first** (run without `--execute`)
2. **Restoration files are important** — keep them!
3. **Duplicate files** are auto-renamed (`_1`, `_2`, ...)
4. **Use quotes** for paths containing spaces

---

## 🐍 Using the API in Python

```python
from app.organizer import FileOrganizer

# Initialize
organizer = FileOrganizer()

# Preview
result = organizer.preview(
    source_dir="C:/Downloads",
    target_dir="C:/Organized"
)
print(f"Preparing to organize {result.total_count} files.")

# Execute
result = organizer.organize(
    source_dir="C:/Downloads",
    target_dir="C:/Organized",
    dry_run=False
)
print(f"Successfully organized {result.success_count} files.")
print(f"Restoration file: {result.restoration_manifest_path}")
```

---

## ❓ FAQ

**Q: Can I exclude certain files?**
A: Yes. The system automatically ignores:

* Hidden files (`.` prefix)
* System folders (`__pycache__`, `node_modules`)
* Temp files (`.tmp`, `.log`, `.bak`)

**Q: Will restored files be exactly the same?**
A: Yes — they are moved back unchanged.

**Q: Can I organize the same folder multiple times?**
A: Yes. Each run creates a new restoration point.

**Q: Can I delete restoration files?**
A: You can, but only if you're sure you won’t need to undo.

---

## 🔧 Advanced Options

```python
organizer = FileOrganizer()

result = organizer.organize(
    source_dir="C:/Downloads",
    target_dir="C:/Organized",
    dry_run=False,                   # False = execute, True = preview
    create_restoration_point=True,   # Enable/disable restoration point
    ignore_patterns=[                # Custom ignore patterns
        "*.tmp",
        "draft_*",
        "backup"
    ]
)
```