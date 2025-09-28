# UV User Manual: Complete Guide to Modern Python Package Management

This comprehensive guide covers how to use **UV**, the modern Python package installer and resolver, with projects utilizing the PEP 621 standard format in their `pyproject.toml` file.

---

## 1. Introduction to UV

UV is a fast, modern replacement for tools like `pip`, `pip-tools`, and `virtualenv`. It offers:
- **Ultra-fast** package resolution and installation
- **Built-in virtual environment management**
- **Full PEP 621 compliance** for modern Python packaging
- **Rust-powered performance** with Python ecosystem compatibility

### 1.1. Installation

Install UV globally using pip or your system package manager:

```bash
# Using pip
pip install uv

# Using pipx (recommended)
pipx install uv

# Using homebrew (macOS/Linux)
brew install uv
```

---

## 2. pyproject.toml Compatibility

### 2.1. Reading the [project] Table

**UV fully supports** the modern **PEP 621** metadata defined under the **`[project]`** table in your `pyproject.toml`.

| pyproject.toml Section | UV Action | Status |
| :--- | :--- | :--- |
| `[build-system]` | Reads `requires` and `build-backend` to handle project setup | **Supported** |
| `[project]` | Reads core metadata: `name`, `version`, `requires-python`, `dependencies` | **Supported** |
| `[project.optional-dependencies]` | Reads and uses these groups when explicitly requested via the `-E` flag | **Supported** |
| `[project.scripts]` | Sets up CLI entry points upon installation | **Supported** |
| `[project.gui-scripts]` | Sets up GUI entry points upon installation | **Supported** |
| `[project.entry-points]` | Registers custom entry points | **Supported** |

### 2.2. Tool Configuration

UV is an installer and resolver; it will **ignore** configuration tables intended for other tools. This requires no modification and is standard practice.

| Tool Configuration Table | UV Action |
| :--- | :--- |
| `[tool.setuptools.*]` | Ignored (Setuptools-specific build configuration) |
| `[tool.pytest.*]` | Ignored (Pytest configuration) |
| `[tool.black]`, `[tool.mypy]`, etc. | Ignored (Formatting, linting, or type-checking configurations) |
| `[tool.uv]` | **Used** for UV-specific configuration |

---

## 3. Project Management Commands

### 3.1. Project Initialization

Create a new Python project with UV:

```bash
# Create a new project
uv init my-project
cd my-project

# Initialize UV in an existing project
uv init

# Create with specific Python version
uv init --python 3.11 my-project
```

### 3.2. Virtual Environment Management

UV automatically manages virtual environments, but you can control them explicitly:

```bash
# Create a virtual environment
uv venv

# Create with specific Python version
uv venv --python 3.11

# Create in custom location
uv venv .venv-custom

# Activate the environment (traditional way)
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Run commands in the environment (UV way)
uv run python script.py
uv run pytest
```

---

## 4. Dependency Management

### 4.1. Installing Dependencies

#### Core Dependencies

```bash
# Install all project dependencies
uv sync

# Install from specific pyproject.toml
uv sync --project /path/to/project

# Install without development dependencies
uv sync --no-dev
```

#### Optional Dependencies (Extras)

```bash
# Install with specific optional groups
uv sync -E dev -E test
uv sync --extra dev --extra test

# Install multiple extras
uv sync -E "dev,test,docs"

# Install all optional dependencies
uv sync --all-extras
```

### 4.2. Adding Dependencies

```bash
# Add a runtime dependency
uv add requests

# Add a development dependency
uv add --dev pytest

# Add to a specific optional group
uv add --optional test pytest-cov

# Add with version constraints
uv add "numpy>=1.20,<2.0"
uv add "django~=4.2.0"

# Add from Git repository
uv add git+https://github.com/user/repo.git

# Add from local path
uv add --editable ./local-package
```

### 4.3. Removing Dependencies

```bash
# Remove a dependency
uv remove requests

# Remove a development dependency
uv remove --dev pytest

# Remove from optional group
uv remove --optional test pytest-cov
```

### 4.4. Updating Dependencies

```bash
# Update all dependencies
uv sync --upgrade

# Update specific package
uv sync --upgrade-package requests

# Update within constraints
uv sync --upgrade-package "django<5.0"
```

---

## 5. Running Commands

### 5.1. Basic Command Execution

```bash
# Run Python scripts
uv run python script.py
uv run python -m module

# Run installed console scripts
uv run pytest
uv run black .
uv run mypy src/

# Run with specific Python version
uv run --python 3.11 python script.py
```

### 5.2. Advanced Execution

```bash
# Run with environment variables
uv run --env-file .env python script.py

# Run with inline dependencies
uv run --with requests python -c "import requests; print(requests.__version__)"

# Run isolated (no project dependencies)
uv run --isolated python script.py

# Run with extra dependencies
uv run --extra dev pytest
```

---

## 6. Lock Files and Reproducible Builds

### 6.1. Lock File Management

```bash
# Generate uv.lock file
uv lock

# Update lock file
uv lock --upgrade

# Install from lock file exactly
uv sync --locked

# Export to requirements.txt format
uv export --format requirements-txt > requirements.txt
uv export --extra dev --format requirements-txt > requirements-dev.txt
```

### 6.2. Cross-Platform Compatibility

```bash
# Generate lock file for specific platforms
uv lock --python-platform linux
uv lock --python-platform windows
uv lock --python-platform darwin

# Generate universal lock file
uv lock --universal
```

---

## 7. Package Installation and Management

### 7.1. Direct Package Installation

```bash
# Install packages (like pip install)
uv pip install requests pandas

# Install from requirements file
uv pip install -r requirements.txt

# Install with constraints
uv pip install --constraint constraints.txt requests

# Install in development mode
uv pip install -e .
uv pip install --editable .
```

### 7.2. Package Information

```bash
# List installed packages
uv pip list

# Show package information
uv pip show requests

# Check for outdated packages
uv pip list --outdated

# Freeze current environment
uv pip freeze
```

---

## 8. Configuration and Settings

### 8.1. UV Configuration File

Create a `uv.toml` or configure in `pyproject.toml`:

```toml
# pyproject.toml
[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
]

# Custom index URLs
index-url = "https://pypi.org/simple"
extra-index-url = ["https://download.pytorch.org/whl/cpu"]

# Environment configuration
environments = ["python_version >= '3.8'"]
```

### 8.2. Environment Variables

```bash
# Set custom cache directory
export UV_CACHE_DIR=/path/to/cache

# Set index URL
export UV_INDEX_URL=https://custom-pypi.org/simple

# Disable cache
export UV_NO_CACHE=1

# Set Python preference
export UV_PYTHON_PREFERENCE=only-managed
```

---

## 9. Advanced Features

### 9.1. Python Version Management

```bash
# List available Python versions
uv python list

# Install specific Python version
uv python install 3.11

# Pin project to specific Python version
uv python pin 3.11

# Find Python installations
uv python find
```

### 9.2. Workspace Management

```bash
# Work with multi-package repositories
uv sync --workspace

# Build workspace packages
uv build --workspace

# Run commands across workspace
uv run --workspace pytest
```

### 9.3. Build and Publish

```bash
# Build distributions
uv build

# Build specific formats
uv build --wheel
uv build --sdist

# Publish to PyPI
uv publish

# Publish to custom index
uv publish --index-url https://custom-pypi.org/
```

---

## 10. Common Workflows

### 10.1. New Project Setup

```bash
# 1. Create project
uv init my-project
cd my-project

# 2. Add dependencies
uv add requests click
uv add --dev pytest black mypy

# 3. Create and sync environment
uv sync

# 4. Run your code
uv run python src/my_project/main.py
```

### 10.2. Existing Project Setup

```bash
# 1. Navigate to project
cd existing-project

# 2. Create virtual environment and install dependencies
uv sync

# 3. Run tests
uv run pytest

# 4. Run development tools
uv run black .
uv run mypy src/
```

### 10.3. CI/CD Pipeline

```bash
# Install UV in CI
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install exact dependencies
uv sync --locked

# Run tests
uv run pytest --cov=src tests/

# Build package
uv build
```

---

## 11. Migration from Other Tools

### 11.1. From pip + virtualenv

```bash
# Old way
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# UV way
uv sync
uv run python script.py
```

### 11.2. From Poetry

```bash
# Convert poetry.lock to uv.lock
uv sync  # UV can read pyproject.toml directly

# Replace common poetry commands
poetry install    → uv sync
poetry add pkg    → uv add pkg
poetry run cmd    → uv run cmd
poetry build      → uv build
```

### 11.3. From pip-tools

```bash
# Old requirements.in/requirements.txt workflow
pip-compile requirements.in
pip-sync requirements.txt

# UV equivalent
uv add package-name  # Adds to pyproject.toml
uv sync             # Installs and creates lock file
```

---

## 12. Troubleshooting

### 12.1. Common Issues

```bash
# Clear UV cache
uv cache clean

# Verbose output for debugging
uv sync --verbose

# Force refresh of package metadata
uv sync --refresh

# Check UV version
uv --version

# Get help for any command
uv --help
uv sync --help
```

### 12.2. Performance Tips

- Use `--no-build-isolation` for faster builds during development
- Set `UV_CACHE_DIR` to a fast storage location
- Use `--frozen` flag in CI for faster installs
- Consider `--no-dev` for production deployments

---

## 13. Best Practices

### 13.1. Project Structure
- Always use `pyproject.toml` for project configuration
- Organize optional dependencies logically (dev, test, docs, etc.)
- Pin Python version requirements appropriately
- Use lock files (`uv.lock`) for reproducible builds

### 13.2. Development Workflow
- Use `uv run` instead of activating virtual environments
- Regularly update dependencies with `uv sync --upgrade`
- Use specific extras for different development needs
- Commit `uv.lock` files to version control

### 13.3. CI/CD Integration
- Always use `uv sync --locked` in CI
- Cache UV's global cache directory
- Use `--frozen` flag for faster CI builds
- Consider using `--no-dev` for production images

---

## Example pyproject.toml Configuration

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-project"
version = "0.1.0"
description = "A sample project using UV"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
requires-python = ">=3.8"
dependencies = [
    "requests>=2.25.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]
test = [
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
]
docs = [
    "sphinx>=5.0.0",
    "sphinx-rtd-theme>=1.0.0",
]

[project.scripts]
my-cli = "my_project.cli:main"

[tool.uv]
dev-dependencies = [
    "ruff>=0.1.0",
]

[tool.uv.sources]
my-local-package = { path = "../my-local-package", editable = true }
```

This manual covers the essential and advanced features of UV for modern Python project management. UV's speed and modern approach make it an excellent choice for both individual developers and large teams working with Python projects.