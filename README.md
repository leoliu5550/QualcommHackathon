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
- [專案程式碼品質與提交規範指南](docs/專案程式碼品質與提交規範指南.md)
- [uv使用說明](docs/uv使用說明.md)
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.