# FileOrg - AI-Powered File Organization

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)
[![PyPI](https://img.shields.io/badge/pypi-v1.0.0-orange)](https://pypi.org/project/fileorg/)

An intelligent file organization system leveraging AI to analyze content and automatically categorize files into meaningful structures.

## Installation

### 📋 Environment Selection Guide

| Environment Type | Use Case | Key Features |
|----------|----------|----------|
| **Development** | Local development, GPU-accelerated training | Full features + CUDA support |
| **CPU-only** | Lightweight deployment, production | CPU-only inference, small footprint |
| **Qualcomm NPU** | Snapdragon device acceleration | NPU hardware-accelerated inference |

### 🚀 Installation Steps

**Step 1: Clone the repository**
```bash
git clone https://github.com/leoliu5550/QualcommHackathon.git
cd QualcommHackathon
```

**Step 2: Choose and install environment dependencies**

*Development environment* (with CUDA support):
```bash
pip install -r requirements-dev.txt
```

*CPU environment* (lightweight):
```bash
pip install -r requirements-cpu.txt
```

*Qualcomm NPU environment*:
```bash
pip install -e ".[dev,qualcomm]"
```

**Step 3: Install the project**
```bash
pip install -e .
```
> 💡 `-e` means editable/development mode installation. Code changes take effect without reinstalling, and the `fileorg` command will be available system-wide

### 🏃‍♂️ Quick Install (One-liner)

**Development environment full installation:**
```bash
git clone https://github.com/leoliu5550/QualcommHackathon.git && cd QualcommHackathon && pip install -r requirements-dev.txt && pip install -e .
```

**CPU environment full installation:**
```bash
git clone https://github.com/leoliu5550/QualcommHackathon.git && cd QualcommHackathon && pip install -r requirements-cpu.txt && pip install -e .
```
### 📦 Install from Github PyPI by pipx (recommended)
```bash
# Install pipx if you don't have it yet
python -m pip install --user pipx
python -m pipx ensurepath

pipx install git+https://github.com/leoliu5550/QualcommHackathon.git
```

### 📦 Install from Github PyPI by pip
```bash
pip install git+https://github.com/leoliu5550/QualcommHackathon.git
```

### 📦 Install from PyPI (Coming Soon)
```bash
pip install fileorg
```


## Quick Start

```bash
# Preview organization structure without moving files
fileorg /path/to/directory --preview

# Organize files
fileorg /path/to/directory

# Restore original structure
fileorg /path/to/directory --restore
```

## Features

- **Content-based classification** using local LLM models
- **Safe preview mode** to review changes before execution
- **Complete restore capability** with automatic backup
- **Comprehensive reports** in HTML and Markdown formats
- **Snapdragon NPU support** for accelerated inference

## System Requirements

### Hardware Requirements
- **Minimum**: Python 3.8+, 4GB RAM
- **Recommended**: Python 3.10+, 8GB RAM, CUDA-compatible GPU
- **Snapdragon NPU**: Qualcomm Snapdragon X Series processors

### Software Dependencies
- **Core**: PyTorch, Transformers, ONNX Runtime
- **File Processing**: python-docx, openpyxl, pypdf, python-pptx
- **Development Tools**: pytest, black, ruff, mypy (dev environment)

## Documentation

### 📚 Online Documentation

Visit our comprehensive documentation at [https://docs.fileorg.com](https://docs.fileorg.com) for:
- Complete API reference
- User guides and tutorials
- Advanced configuration options
- Examples and best practices

### 🛠️ Building Documentation Locally

#### Prerequisites
Install documentation dependencies:
```bash
pip install -r requirements-docs.txt
```

#### Local Development Server
Run the documentation server locally for development:
```bash
mkdocs serve
```
This will start a development server at `http://127.0.0.1:8000/` with live reloading.

#### Building Static Documentation
Build the static documentation site:
```bash
mkdocs build
```
The built documentation will be in the `site/` directory.

#### Deploying to GitHub Pages
Deploy documentation to GitHub Pages (requires push permissions):
```bash
mkdocs gh-deploy
```
This command builds the documentation and pushes it to the `gh-pages` branch.

### 📝 Documentation Structure

```
docs/
├── index.md              # Homepage
├── getting-started/      # Installation and setup guides
├── user-guide/           # User documentation
├── api/                  # API reference (auto-generated)
├── examples/             # Code examples
├── development/          # Developer guides
└── advanced/             # Advanced topics
```

### 🔧 Configuration

Documentation is configured via `mkdocs.yml` with:
- **Theme**: Material for MkDocs
- **Plugins**: mkdocstrings for automatic API documentation
- **Features**: Search, dark mode, code highlighting
- **Custom Domain**: https://docs.fileorg.com

## Contributing

We welcome contributions. Please see our [contributing guidelines](CONTRIBUTING.md) for details.

## Acknowledgments

Originally developed for the Qualcomm Hackathon, FileOrg continues to evolve with community contributions.

## License

MIT License - see [LICENSE](LICENSE) for details.