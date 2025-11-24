# FileOrg - AI-Powered File Organization

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)

Intelligent file organization tool using AI to analyze and categorize documents automatically.

## Features

- **AI Content Analysis** - Smart document type and content detection using LLM
- **Auto Categorization** - Creates meaningful folder structures
- **Safe Preview** - Review changes before execution
- **One-Click Restore** - Complete backup and restoration from `.backup/`
- **Batch Processing** - Fast organization of large file collections
- **Flexible LLM Backend** - Supports TURU API, GPU (CUDA), CPU, MPS, and QAIC

## Supported File Formats

PDF, Word (`.docx`), Excel (`.xlsx`), PowerPoint (`.pptx`), TXT, HTML, JSON, CSV, XML, Markdown

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Install uv (if not already installed)

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation Options

#### Option 1: Basic Installation (TURU API Mode)

For use with TURU API server (lightweight, no PyTorch):

```bash
uv pip install -e .
```

#### Option 2: Full Installation (GPU/CPU Mode)

For running LLM locally with PyTorch (recommended for most users):

```bash
uv pip install -e .[non-npu]
```

This installs additional dependencies:
- `torch` (PyTorch with CUDA support)
- `transformers` (HuggingFace models)
- `accelerate` (Model acceleration)
- `numpy`, `sentencepiece`, `protobuf`

**For GPU support (NVIDIA):**

```bash
# Uninstall CPU-only PyTorch first (if already installed)
uv pip uninstall torch torchvision torchaudio

# Install PyTorch with CUDA 12.1 support
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## Quick Start

### 1. Organize Files

```bash
# Preview mode (dry-run, no actual file movement)
fileorg organize --path /path/to/directory --preview

# Execute organization
fileorg organize --path /path/to/directory

# With custom character limit for parsing
fileorg organize --path /path/to/directory --char-limit 1000
```

**What happens:**
1. **Checks for existing backup** - If `.backup/file_paths.json` exists, prompts:
   - **Option 1**: Use existing backup (fast, skip LLM) ⚡
   - **Option 2**: Re-organize (run full LLM classification again)
   - **Option 3**: Restore (undo previous organization)
   - **Option 4**: Cancel
2. Scans all files in the directory
3. Parses file contents (up to `char-limit` characters per file)
4. Uses LLM to classify files into categories
5. Creates `.backup/file_paths.json` with relative paths
6. Moves files to organized folders (skipped in `--preview` mode)

**Smart backup detection benefits:**
- **Option 1** avoids expensive LLM inference (instant execution)
- Useful when you want to re-execute the same organization plan
- Offers quick restore without separate command
- Prevents accidental overwrite of existing organization

### 2. Restore Files

```bash
fileorg restore --path /path/to/directory
```

**What happens:**
1. Reads `.backup/file_paths.json`
2. Moves all files back to their original locations
3. Removes empty directories

## LLM Provider Selection

FileOrg automatically detects the best available LLM provider in this priority order:

1. **TURU API** (if running at `http://127.0.0.1:8000`) - Recommended
2. **QAIC** (Qualcomm AI Engine) - For Qualcomm hardware
3. **CUDA GPU** (NVIDIA) - For NVIDIA GPUs
4. **MPS** (Apple Silicon) - For M1/M2/M3 Macs
5. **CPU** (fallback) - Slowest, requires PyTorch

### Using TURU API Server (NPU Acceleration)

TURU provides the fastest inference using Qualcomm NPU hardware.

**1. Start TURU Server**

```bash
# Start TURU server in another terminal
# Default: http://127.0.0.1:8000
# (See TURU documentation for setup instructions)
```

**2. Configure TURU (Optional)**

Create `.env` file to customize TURU settings:

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Available environment variables:**

```bash
# TURU API endpoint (default: http://127.0.0.1:80/v1.0)
TURU_BASE_URL=http://127.0.0.1:80/v1.0

# NPU model to use (default: .bot/Llama 3.1 8B @NPU)
TURU_MODEL=.bot/Llama 3.1 8B @NPU

# API key (default: API_KEY)
TURU_API_KEY=API_KEY

# Temperature for sampling (default: 0.1)
TURU_TEMPERATURE=0.1

# Request timeout in seconds (default: 600.0)
TURU_TIMEOUT=600.0
```

**3. Run FileOrg**

```bash
# FileOrg will auto-detect TURU server
fileorg organize --path /path/to/directory
```

**Common NPU Models:**
- `.bot/Llama 3.1 8B @NPU` (default, recommended)
- `.bot/Llama 3.2 3B @NPU` (faster, lower accuracy)
- `.bot/Qwen 2.5 7B @NPU` (alternative)

### Character Limit

Control how much content is extracted from each file:

```bash
fileorg organize --path /path/to/dir --char-limit 500  # Fast, less accurate
fileorg organize --path /path/to/dir --char-limit 5000 # Slower, more accurate
```

### Code Quality

See [Development Guide](docs/專案程式碼品質與提交規範指南.md) for:
- Code style guidelines
- Commit message conventions
- Testing requirements

### Using uv

See [uv Usage Guide](docs/uv使用說明.md) for package management with uv.


## Contributing

Issues and Pull Requests are welcome! Please follow the development guidelines.

## License

This project is licensed under the GNU General Public License v3 - see the [LICENSE](LICENSE) file for details.

## Authors

- Leo Liu - [leoliu5550@gmail.com](mailto:leoliu5550@gmail.com)
- Yide Lin - [lin.yide.doris@gmail.com](mailto:lin.yide.doris@gmail.com)
- Joel Hsu - [jieyao.hsu.efef31016@gmail.com](mailto:jieyao.hsu.efef31016@gmail.com)
- Steven Ye - [bingjunye4@gmail.com](mailto:bingjunye4@gmail.com)

## Acknowledgments

Built for the Qualcomm Hackathon using Qualcomm AI technologies.
