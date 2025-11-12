# IFileScanner adaptor

* **Process Overview (Flow Description)**
* **Ignore Pattern Configuration Explanation**

You can paste this directly under your existing module-level docstring or in your README.

---

## 📘 Module Flow Description (File Scanner Module)

This module is responsible for the **directory scanning workflow** within the FileOrg system.
It recursively scans a target directory, collecting essential metadata (path, name, size) for each file while automatically excluding irrelevant or system-generated files according to ignore rules.

### Workflow Summary

1. **Initialization (`__init__`)**

   * The user creates a `FileScanner(root_dir, ignore_patterns)` instance.
   * The module validates whether the target directory exists and is a valid folder.
   * Ignore patterns are configured (either user-provided or defaults).


2. **Recursive Scanning (`scan` / `_scan`)**

   * The scanning starts from `root_dir` and descends into subdirectories.

   * For each item encountered:

     * If it matches any ignore pattern (`_is_ignored()`), it is skipped.
     * If it’s a directory, scanning continues recursively.
     * If it’s a file, metadata such as path, name, and size are collected.

   * **Output:** `ScanOutput` — a list of file metadata dictionaries:

    ```python
    [
        {'path': '/tests/example_data/file1.pdf', 'name': 'file1.pdf', 'size': 1339552},
        ...
    ]
    ```

3. **Report Generation (`generate_report`)**

   * Aggregates scanning results into a structured summary that includes:

     * Total file count (`file_count`)
     * Total file size (`total_size`)
     * Detailed file list (`files`) — the content of `scan()` is embedded here

   * **Output:** `ReportOutput` — a dictionary with additional metadata:

    ```python
    {
        'root': '/Users/leo/Documents/Projects',
        'file_count': 15,
        'total_size': 6744401,
        'files': [ ... scan() output here ... ]
    }
    ```

* **Key Difference:** Unlike `scan()`, `generate_report()` provides the overall summary and aggregates the results, but you do not need to call `scan()` beforehand unless you want the raw scan output separately.

4. **Report Output (`save_report`)**

   * Converts a `ReportOutput` into JSON format and saves it to disk.
   * **Behavior:** You can call `save_report()` directly with a specified file path; there is **no need to call `scan()` or `generate_report()` first**. You can also pass an existing `ReportOutput` if desired.

```python
scanner.save_report(output_path="scan_report.json")
```

---

## Ignore Pattern Configuration

The module uses **glob-style pattern matching** to filter out files and directories that should be excluded during scanning.
This is handled internally by the `_is_ignored()` method using the `fnmatch` library.

### Default Ignore Rules (`DEFAULT_IGNORE_PATTERNS`)

```python
DEFAULT_IGNORE_PATTERNS = [
    ".*",           # Hidden files and folders (e.g., .git, .env)
    "__pycache__",  # Python bytecode cache
    "node_modules", # Node.js dependency folder
    "*.tmp",        # Temporary files
    "*.log",        # Log files
    "*.bak",        # Backup files
    "Thumbs.db",    # Windows system cache
    ".DS_Store",    # macOS system cache
]
```

### Custom Ignore Rules

Users can provide their own ignore list at initialization:

```python
custom_patterns = ["*.cache", "*.old", "temp_*"]
scanner = FileScanner("/Users/leo/Documents", ignore_patterns=custom_patterns)
```

In this case, the scanner will use **only** the provided patterns and ignore the defaults.

To extend (rather than replace) the default rules:

```python
scanner = FileScanner(
    "/Users/leo/Documents",
    ignore_patterns=FileScanner.DEFAULT_IGNORE_PATTERNS + ["*.bak", "test_*"]
)
```

### Pattern Matching Logic

* The comparison is made using `fnmatch.fnmatch(path.name, pattern)`.
* Matching applies to **file/directory names only**, not the full path.
* Examples:

  * `"*.log"` → ignores all `.log` files.
  * `"test_*"` → ignores files/folders starting with `test_`.
  * `".*"` → ignores hidden files (those starting with a dot).

---

## Simplified Flow Diagram

```text
FileScanner()
    │
    ├── validate root_dir
    │
    ├── scan()
    │     └── _scan(directory)
    │           ├── skip ignored (via _is_ignored)
    │           ├── if dir → recurse
    │           └── if file → collect metadata
    │
    ├── generate_report()
    │     └── aggregate total size / count
    │
    └── save_report()
          └── write JSON report file
```
---

# Usage Example

The following example demonstrates how to initialize the `FileScanner`, perform a scan, generate a report, and export it as a JSON file.

```python
from fileorg.file_ops.scanner import FileScanner

def main():
    # 1. Define the target directory for scanning
    target_dir = "/Users/leo/Documents/Projects"

    # 2. (Optional) Define custom ignore patterns
    custom_ignores = [
        "*.tmp", "*.log", "build", "__pycache__", ".git", "*.bak"
    ]

    # 3. Initialize the scanner
    scanner = FileScanner(root_dir=target_dir, ignore_patterns=custom_ignores)

    # 4. Perform the scan and generate a report
    report = scanner.generate_report()

    # 5. Print basic report information
    print("=== File Scan Report ===")
    print(f"Root Directory : {report['root']}")
    print(f"Total Files    : {report['file_count']}")
    print(f"Total Size     : {report['total_size']} bytes")

    # 6. Save the detailed report to a JSON file
    output_file = "scan_report.json"
    scanner.save_report(output_file)
    print(f"\nReport saved to: {output_file}")

if __name__ == "__main__":
    main()
```

### Expected Output (Console)

```
=== File Scan Report ===
Root Directory : /Users/leo/Documents/Projects
Total Files    : 128
Total Size     : 45,372,111 bytes

Report saved to: scan_report.json
```

### Example Output File (`scan_report.json`)

```json
{
    "root": "/Users/leo/Documents/Projects",
    "file_count": 128,
    "total_size": 45372111,
    "files": [
        {
            "path": "/Users/leo/Documents/Projects/main.py",
            "name": "main.py",
            "size": 2048
        },
        {
            "path": "/Users/leo/Documents/Projects/utils/helpers.py",
            "name": "helpers.py",
            "size": 3890
        }
    ]
}
```