# FileOrg CLI Tool Documentation

A command-line tool that can be installed in development mode or globally using `uv`, providing a convenient `fileorg` command for file organization.

## Installation Methods

### Development Mode (Editable Install)

Install `fileorg` into your current virtual environment. Code changes will be immediately reflected without reinstallation, making this ideal for active development.

```bash
uv pip install -e .
```

**Usage:**
```bash
fileorg -p tests/example_data/entertainment --output tests --preview --char-limit 100
```

> **Note:** The executable will be located at `.venv/bin/fileorg`

---

### Global Installation (Production Use)

Install as a standalone tool with an independent execution environment. The `fileorg` command will be available system-wide from `~/.local/bin`.

```bash
uv tool install .
```

**Verify installation:**
```bash
uv tool list
# Expected output:
# Installed tools:
#   fileorg 0.1.0  /path/to/your/project
```

**Usage:**
```bash
fileorg -p tests/example_data/entertainment --output tests --preview --char-limit 100
```

> **Tip:** If you encounter a "No such file or directory" error, the virtual environment path from a previous installation may be invalid. Run `uv tool uninstall fileorg` and reinstall.

---

## Uninstallation

### For Development Mode Installation:
```bash
uv pip uninstall fileorg
```

### For Global Installation:
```bash
uv tool uninstall fileorg
```

---

## Development Testing (No Installation Required)

For quick testing, debugging, or parameter validation without installation, run the module directly:

```bash
uv run -m fileorg.main -p tests/example_data/entertainment --output tests --preview --char-limit 100
```

> 💡 **Advantage:** This creates a temporary execution environment without installing anything, perfect for rapid development iterations.

---

## Troubleshooting

### Error: `bash: .../fileorg: No such file or directory`

**Cause:** A previous `uv tool install .` installation created a reference to an outdated `.venv` directory.

**Solution:**
```bash
uv tool uninstall fileorg
uv tool install . --force
```

---

### Error: `uv pip uninstall fileorg` reports "not installed"

**Cause:** The package name in `pyproject.toml` doesn't match the name you're attempting to uninstall.

**Solution:**

1. Check the `name` field in your `pyproject.toml`:
   ```toml
   [project]
   name = "fileorg"
   ```

2. Use the exact name from the config:
   ```bash
   uv pip uninstall fileorg
   ```
   
   If the actual name differs (e.g., `aprss`), use that name instead.

---

## Project Structure

```
.
├── fileorg/
│   ├── __init__.py
│   └── main.py
├── pyproject.toml
└── README.md
```

### Example `pyproject.toml`

```toml
[project]
name = "fileorg"
version = "0.1.0"
requires-python = ">=3.13"

[project.scripts]
fileorg = "fileorg.main:main"
```

---

## Quick Start Example

```bash
fileorg -p tests/example_data/entertainment --output tests --preview --char-limit 100
```

This command:
- Processes files from `tests/example_data/entertainment`
- Outputs results to `tests`
- Shows a preview before execution
- Limits character processing to 100 characters