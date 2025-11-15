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

Choose the installation method that best fits your use case:

| Use Case | Installation | Size | Startup Speed | Best For |
|----------|-------------|------|---------------|----------|
| **NPU Acceleration** | Option 1 | ~2 GB | Fastest | Qualcomm hardware with TURU |
| **Lightweight Runtime** | Option 2 | ~2 GB | Fast | Production deployment |
| **Full Local LLM** | Option 3 | ~10 GB | Slow | Development & customization |

---

#### Option 1: TURU API Mode (NPU Acceleration)

**Best for:** Qualcomm NPU hardware with TURU server running

```bash
# Install lightweight runtime
uv pip install -e .

# Use with TURU server (see TURU configuration section below)
fileorg organize --path /path/to/directory
```

> **Note:** TURU server must be running at `http://127.0.0.1:8000` (see [TURU Configuration](#using-turu-api-server-npu-acceleration))

---

#### Option 2: ONNX Runtime (Lightweight & Fast)

**Best for:** Production use without heavy PyTorch dependencies

```bash
# 1. Install lightweight runtime (~2 GB, NO PyTorch)
uv pip install -e .

# 2. Download pre-exported ONNX model (~6 GB, one-time)
python scripts/download_onnx_model.py

# 3. Start using immediately
fileorg organize --path /path/to/directory
```

**Benefits:**
- 5-10x faster startup than PyTorch
- 80% smaller installation size
- Multi-platform: CUDA, CoreML, Qualcomm NPU, CPU

<details>
<summary><b>Advanced: Export your own models</b> (developers only)</summary>

```bash
# Install export dependencies (~10 GB)
uv pip install -e '.[llm-export]'

# Export model
fileorg-export-llm --yes
```
</details>

---

#### Option 3: PyTorch Full Installation (GPU/CPU)

**Best for:** Development or when you need full PyTorch flexibility

```bash
# Install with PyTorch dependencies (~10 GB)
uv pip install -e .[non-npu]
```

<details>
<summary><b>NVIDIA GPU Support</b></summary>

```bash
# If you need CUDA 12.1 support, reinstall PyTorch:
uv pip uninstall torch torchvision torchaudio
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```
</details>

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
   - **Option 1**: Use existing backup (fast, skip LLM)
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

## LLM Provider Auto-Detection

FileOrg **automatically selects** the best available LLM provider:

| Priority | Provider | Hardware | Speed |
|----------|----------|----------|-------|
| 1 | **TURU API** | Qualcomm NPU | Fastest |
| 2 | **ONNX Runtime** | CUDA/CoreML/QNN/CPU | Fast |
| 3 | **QAIC** | Qualcomm AI Engine | Fast |
| 4 | **CUDA** | NVIDIA GPU | Medium |
| 5 | **MPS** | Apple Silicon | Medium |
| 6 | **CPU** | Any (fallback) | Slow |

> **No configuration needed** - FileOrg will use the fastest available option automatically.

### Using TURU API Server (NPU Acceleration)

TURU provides the fastest inference using Qualcomm NPU hardware.

<details>
<summary><b>TURU Setup & Configuration</b></summary>

**1. Start TURU Server**
```bash
# Start TURU server in another terminal (default: http://127.0.0.1:8000)
# See TURU documentation for setup instructions
```

**2. Configure Environment (Optional)**

Create `.env` file to customize settings:

```bash
cp .env.example .env
```

Edit with your preferences:
```bash
TURU_BASE_URL=http://127.0.0.1:8000/v1
TURU_MODEL=.bot/Llama 3.1 8B @NPU      # Options: Llama 3.1 8B, Llama 3.2 3B, Qwen 2.5 7B
TURU_API_KEY=API_KEY
TURU_TEMPERATURE=0.1
TURU_TIMEOUT=600.0
```

**3. Run FileOrg**
```bash
fileorg organize --path /path/to/directory  # Auto-detects TURU
```
</details>

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
