# FileOrg - AI-Powered File Organization

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)

Intelligent file organization tool using AI to analyze and categorize documents automatically.

## Installation

### Install from GitHub (Recommended)

#### Using pipx (Isolated environment)
```bash
pipx install git+https://github.com/leoliu5550/QualcommHackathon.git
```

### Development Installation
```bash
git clone https://github.com/leoliu5550/QualcommHackathon.git
cd QualcommHackathon
pip install -e .              # Basic installation
pip install -e ".[dev]"       # With development tools
pip install -e ".[non-npu]"   # With CPU/GPU model support
pip install -e ".[docs]"      # With documentation tools
```

### Installation Options
- **Default**: NPU API client (httpx) - smallest footprint
- **[non-npu]**: PyTorch + Transformers for CPU/GPU inference
- **[dev]**: Testing and code quality tools
- **[docs]**: Documentation generation tools

> Note: PyPI package coming soon. Currently install from GitHub.

## Usage

### GUI Interface
```bash
fileorg start
```
> Opens graphical interface with drag-and-drop support

### Command Line
```bash
fileorg /path/to/folder           # Organize folder
fileorg /path/to/folder --preview # Preview mode (no file movement)
fileorg /path/to/folder --restore # Restore original structure
```

### Windows Context Menu
```batch
# Install context menu
cd rkey_registry
install_key.bat

# Uninstall context menu
uninstall_key.bat
```
> Right-click any folder to see "Organize with FileOrg" option

## Configuration

Edit `fileorg/ai/config.py`:
```python
"backend": "qualcomm"  # Use NPU API (default)
"backend": "local"     # Use local CPU/GPU (requires [non-npu] installation)
```

## Key Features

- **AI Content Analysis** - Smart document type and content detection
- **Auto Categorization** - Creates meaningful folder structures
- **Safe Preview** - Review changes before execution
- **One-Click Restore** - Complete backup and restoration
- **Batch Processing** - Fast organization of large file collections

## Supported Formats

PDF, Word, Excel, PowerPoint, TXT, HTML, JSON, CSV, XML, Markdown

## Contributing

Issues and Pull Requests are welcome!

## Media & Feedback
> **官方評語 (Qualcomm Feedback):** "The project delivers a complete solution that fully harnesses the Snapdragon X Elite NPU to showcase the power of on-device AI, creating an impressive and highly personalized user experience."
>
> **相關報導 (Related News):** [Yahoo News](https://tw.stock.yahoo.com/news/%E9%A6%96%E5%B1%8F-%E9%AB%98%E9%80%9A%E5%8F%B0%E7%81%A3ai%E9%BB%91%E5%AE%A2%E6%9D%BE-%E5%9C%93%E6%BB%A1%E8%90%BD%E5%B9%95-%E4%B8%89%E5%BC%B7%E5%9C%98%E9%9A%8A%E5%B1%95%E7%8F%BE%E9%82%8A%E7%B7%A3ai%E5%89%B5%E6%96%B0%E5%AF%A6%E5%8A%9B-010835638.html)

## License

This project is licensed under the GPL v3 License - see the [LICENSE](LICENSE) file for details.