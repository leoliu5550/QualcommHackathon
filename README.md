# FileOrg - AI-Powered File Organization

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)
[![PyPI](https://img.shields.io/badge/pypi-v1.0.0-orange)](https://pypi.org/project/fileorg/)

An intelligent file organization system leveraging AI to analyze content and automatically categorize files into meaningful structures.

## Installation

### From PyPI
```bash
pip install fileorg
```

### From Source
```bash
git clone https://github.com/yourusername/fileorg.git
cd fileorg
pip install -e .
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

## Requirements

- Python 3.8+
- 8GB RAM recommended
- CUDA-compatible GPU (optional)

## Documentation

For detailed documentation, API reference, and advanced configuration options, visit our [GitHub Pages](https://yourusername.github.io/fileorg).

## Contributing

We welcome contributions. Please see our [contributing guidelines](CONTRIBUTING.md) for details.

## Acknowledgments

Originally developed for the Qualcomm Hackathon, FileOrg continues to evolve with community contributions.

## License

MIT License - see [LICENSE](LICENSE) for details.