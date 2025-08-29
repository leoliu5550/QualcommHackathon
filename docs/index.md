# FileOrg Documentation

**Intelligent File Organization Powered by AI**

[![GitHub Stars](https://img.shields.io/github/stars/leoliu5550/QualcommHackathon)](https://github.com/leoliu5550/QualcommHackathon)
[![License](https://img.shields.io/github/license/leoliu5550/QualcommHackathon)](https://github.com/leoliu5550/QualcommHackathon/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://pypi.org/project/fileorg/)

## Transform Your Digital Chaos into Organized Structure

FileOrg is an AI-powered file organization system that understands your documents, categorizes them intelligently, and creates a perfectly organized folder structure - all automatically.

## Key Features

### AI-Powered Classification
Uses advanced language models to understand file content and categorize intelligently based on actual document meaning, not just filenames.

### Multi-Format Support  
Handles PDFs, Word documents, Excel sheets, presentations, and more with specialized parsers for each format.

### Hardware Acceleration
Supports GPU acceleration and Qualcomm Snapdragon NPU optimization for blazing-fast processing.

### Safe & Reversible
Complete backup and restore functionality ensures your files are always safe with one-command rollback.

### Comprehensive Reports
Generates detailed reports with visualizations of your organized structure in HTML and Markdown formats.

### Cross-Platform
Works seamlessly on Windows, macOS, and Linux environments.

## How It Works

```
Messy Folder → File Discovery → Content Extraction → AI Analysis → Smart Categorization → Clean Structure → Visual Report
```

## Quick Start

### Command Line

```bash
# Install FileOrg
pip install fileorg

# Organize a folder
fileorg /path/to/messy/folder

# Preview without moving files
fileorg /path/to/folder --preview

# Restore original structure
fileorg /path/to/folder --restore
```

### Python API

```python
from fileorg import Organizer

# Create organizer instance
organizer = Organizer()

# Start organization
organizer.start_organize("/path/to/folder")
```

## What Makes FileOrg Special

### Intelligent Understanding
Unlike simple file organizers that only look at file names or extensions, FileOrg actually reads and understands your documents. It uses state-of-the-art language models to analyze content and make intelligent categorization decisions.

### Hardware Flexibility
FileOrg adapts to your hardware:
- **GPU Acceleration**: Leverages NVIDIA/AMD GPUs for fast processing
- **NPU Support**: Optimized for Snapdragon X Elite laptops
- **CPU Fallback**: Works on any machine, even without specialized hardware

### Privacy First
All processing happens locally on your machine. Your documents never leave your computer, ensuring complete privacy and security.

## Performance Benchmarks

| Hardware | Files/Minute | Model |
|----------|-------------|-------|
| RTX 4090 | 500+ | Llama 3.2 |
| Snapdragon X Elite | 300+ | TinyLlama |
| CPU (i7-12700) | 100+ | TinyLlama |

## Supported File Types

**Documents**: PDF, DOCX, TXT, MD  
**Spreadsheets**: XLSX, CSV  
**Presentations**: PPTX, PPT  
**Data**: JSON, XML, HTML

## Documentation

- [Getting Started](getting-started/installation.md) - Installation guide and your first organization
- [User Guide](user-guide/cli.md) - Detailed usage instructions and best practices
- [API Reference](api/index.md) - Complete API documentation for developers

## Contributing

We welcome contributions! FileOrg is open-source and community-driven.

- [GitHub Repository](https://github.com/leoliu5550/QualcommHackathon)
- [Issue Tracker](https://github.com/leoliu5550/QualcommHackathon/issues)

## License

FileOrg is released under the MIT License. See [LICENSE](https://github.com/leoliu5550/QualcommHackathon/blob/main/LICENSE) for details.

---

Made with dedication by the FileOrg Team