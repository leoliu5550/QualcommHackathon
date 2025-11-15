# FileOrg CLI Tool Documentation

A command-line tool that can be installed in development mode or globally using `uv`, providing a convenient `fileorg` command for file organization.

## Quick Installation Guide

### Which Installation Method Should I Use?

| Scenario | Method | Command |
|----------|--------|---------|
| **Active development** (modifying code) | Development Mode | `uv pip install -e .` |
| **Production use** (standalone tool) | Global Installation | `uv tool install .` |
| **Testing without installation** (quick iterations) | Development Testing | `uv run -m fileorg.main` |

---

## Installation Methods

### Development Mode (Editable Install)

Install `fileorg` into your current virtual environment. Code changes will be immediately reflected without reinstallation, making this ideal for active development.

**Basic installation (without LLM dependencies):**
```bash
uv pip install -e .
```

**With LLM support (CPU/GPU mode, installs torch, transformers, etc.):**
```bash
uv pip install -e .[non-npu]
```

> **⚠️ Important for zsh users:**
> zsh interprets `.[non-npu]` as a glob pattern. To avoid shell expansion errors, wrap the argument in quotes:
> ```bash
> uv pip install -e ".[non-npu]"
> ```

**Usage:**
```bash
fileorg organize --path tests/example_data/entertainment --preview --char-limit 100
```

> **Note:**
> - The executable will be located at `.venv/bin/fileorg`
> - If using CPU/GPU mode, you need `[non-npu]` dependencies
> - If using TURU API server, basic installation is sufficient

---

### Global Installation (Production Use)

Install as a standalone tool with an independent execution environment. The `fileorg` command will be available system-wide from `~/.local/bin`.

**Basic installation:**
```bash
uv tool install .
```

**With LLM support (CPU/GPU mode):**
```bash
uv tool install ".[non-npu]"
```

> **⚠️ Important for zsh users:**
> As mentioned above, remember to quote the extras argument to prevent shell glob pattern expansion:
> ```bash
> uv tool install ".[non-npu]"
> ```

**Verify installation:**
```bash
uv tool list
# Expected output:
# Installed tools:
#   fileorg 0.1.0  /path/to/your/project
```

**Usage:**
```bash
fileorg organize --path tests/example_data/entertainment --preview --char-limit 100
```

> **Tip:** If you encounter a "No such file or directory" error, the virtual environment path from a previous installation may be invalid. Run `uv tool uninstall fileorg` and reinstall.

---

## Installation Methods Comparison

### `uv pip install -e .` (Development Mode) vs `uv tool install .` (Global Installation)

| Aspect | `uv pip install -e .` | `uv tool install .` |
|--------|----------------------|---------------------|
| **Installation Scope** | Installs into current virtual environment | Creates isolated virtual environment in `~/.local/bin` |
| **Command Availability** | Available in current environment only | Available system-wide from any directory |
| **Code Changes Reflection** | Immediate (editable install) | Requires reinstallation to reflect changes |
| **Use Case** | Active development | Production/standalone tool usage |
| **Executable Location** | `.venv/bin/fileorg` | `~/.local/bin/fileorg` |
| **Virtual Environment** | Shares with your project `.venv` | Independent isolated environment |
| **Dependencies Impact** | Affects project environment | Isolated, won't affect other projects |

**Summary:**
- Choose **`uv pip install -e .`** if you're developing and modifying code frequently
- Choose **`uv tool install .`** if you want a standalone tool that won't interfere with your project dependencies

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

**Basic (without LLM):**
```bash
uv run -m fileorg.main organize --path tests/example_data/entertainment --preview --char-limit 100
```

**With LLM support:**
```bash
uv run --extra non-npu -m fileorg.main organize --path tests/example_data/entertainment --preview --char-limit 100
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

### Organize Files
```bash
fileorg organize --path tests/example_data/entertainment --preview --char-limit 100
```

This command:
- Processes files from `tests/example_data/entertainment`
- Creates backup in `tests/example_data/entertainment/.backup`
- Shows a preview before execution (no actual file movement)
- Limits character processing to 100 characters

### Restore Files
```bash
fileorg restore --path tests/example_data/entertainment
```

This command:
- Restores files from `tests/example_data/entertainment/.backup`
- Moves all files back to their original locations