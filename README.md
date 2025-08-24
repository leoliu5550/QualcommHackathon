# FileOrg - AI-Powered File Organization

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)
[![PyPI](https://img.shields.io/badge/pypi-v1.0.0-orange)](https://pypi.org/project/fileorg/)

An intelligent file organization system leveraging AI to analyze content and automatically categorize files into meaningful structures.

## Installation

### 📋 環境選擇指南

| 環境類型 | 使用場景 | 特色功能 |
|----------|----------|----------|
| **開發環境** | 本地開發、GPU 加速訓練 | 完整功能 + CUDA 支援 |
| **CPU 環境** | 輕量部署、生產環境 | 僅 CPU 推理，體積小 |
| **Qualcomm NPU** | Snapdragon 裝置加速 | NPU 硬體加速推理 |

### 🚀 安裝步驟

**步驟 1: 下載專案**
```bash
git clone https://github.com/leoliu5550/QualcommHackathon.git
cd QualcommHackathon
```

**步驟 2: 選擇並安裝環境依賴**

*開發環境* (包含 CUDA 支援):
```bash
pip install -r requirements-dev.txt
```

*CPU 環境* (輕量化):
```bash
pip install -r requirements-cpu.txt
```

*Qualcomm NPU 環境*:
```bash
pip install -e ".[dev,qualcomm]"
```

**步驟 3: 安裝專案本身**
```bash
pip install -e .
```
> 💡 `-e` 代表開發模式安裝，修改程式碼後無需重新安裝，`fileorg` 命令將在系統中可用

### 🏃‍♂️ 快速安裝 (一鍵複製)

**開發環境完整安裝:**
```bash
git clone https://github.com/leoliu5550/QualcommHackathon.git && cd QualcommHackathon && pip install -r requirements-dev.txt && pip install -e .
```

**CPU 環境完整安裝:**
```bash
git clone https://github.com/leoliu5550/QualcommHackathon.git && cd QualcommHackathon && pip install -r requirements-cpu.txt && pip install -e .
```

### 📦 從 PyPI 安裝 (即將推出)
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

### 硬體需求
- **最低需求**: Python 3.8+, 4GB RAM
- **建議配置**: Python 3.10+, 8GB RAM, CUDA-compatible GPU
- **Snapdragon NPU**: Qualcomm Snapdragon X 系列處理器

### 軟體相依性
- **核心依賴**: PyTorch, Transformers, ONNX Runtime
- **文件處理**: python-docx, openpyxl, pypdf, python-pptx
- **開發工具**: pytest, black, ruff, mypy (開發環境)

## Documentation

For detailed documentation, API reference, and advanced configuration options, visit our [GitHub Pages](https://yourusername.github.io/fileorg).

## Contributing

We welcome contributions. Please see our [contributing guidelines](CONTRIBUTING.md) for details.

## Acknowledgments

Originally developed for the Qualcomm Hackathon, FileOrg continues to evolve with community contributions.

## License

MIT License - see [LICENSE](LICENSE) for details.