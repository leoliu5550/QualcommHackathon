# Installation Guide

## System Requirements

### Minimum Requirements
- **Python**: 3.11 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 500MB for installation + space for models
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+

### Recommended Requirements
- **GPU**: NVIDIA GPU with CUDA support (optional)
- **NPU**: Qualcomm Snapdragon X Elite (optional)
- **RAM**: 16GB for optimal performance
- **Storage**: 2GB for models and cache

## Installation Methods

### Method 1: Install from GitHub (Recommended)

=== "Using pipx (Isolated Environment)"

    ```bash
    # Install pipx if not already installed
    python -m pip install --user pipx
    python -m pipx ensurepath
    
    # Install FileOrg
    pipx install git+https://github.com/leoliu5550/QualcommHackathon.git
    
    # Verify installation
    fileorg --version
    ```

=== "Direct pip Installation"

    ```bash
    # Install directly with pip
    pip install git+https://github.com/leoliu5550/QualcommHackathon.git
    
    # Verify installation
    fileorg --version
    ```

### Method 2: Development Installation

```bash
# Clone repository
git clone https://github.com/leoliu5550/QualcommHackathon.git
cd QualcommHackathon

# Basic installation (NPU API mode)
pip install -e .

# With CPU/GPU model support
pip install -e ".[non-npu]"

# With development tools
pip install -e ".[dev]"

# With documentation tools
pip install -e ".[docs]"

# All extras
pip install -e ".[non-npu,dev,docs]"
```

### Installation Options Explained

- **Default Installation**: Includes NPU API client (httpx) for Qualcomm backend - smallest footprint
- **[non-npu]**: Adds PyTorch + Transformers for local CPU/GPU inference
- **[dev]**: Adds testing and code quality tools (pytest, black, mypy)
- **[docs]**: Adds documentation generation tools (mkdocs)

## Platform-Specific Instructions

### Windows

#### Using pip

```powershell
# Open PowerShell as Administrator
python -m pip install --upgrade pip

# Install from GitHub
pip install git+https://github.com/leoliu5550/QualcommHackathon.git

# Or use pipx for isolated environment
pipx install git+https://github.com/leoliu5550/QualcommHackathon.git

# Add to PATH if needed
$env:Path += ";$env:USERPROFILE\.local\bin"
```

#### Right-Click Integration

For Windows context menu integration:

```batch
# Navigate to the cloned repository
cd QualcommHackathon\rkey_registry

# Install context menu (Run as Administrator)
install_key.bat

# To uninstall later
uninstall_key.bat
```

Now you can right-click any folder and select "Organize with FileOrg"

### macOS

```bash
# Install Python via Homebrew
brew install python@3.11

# Install FileOrg from GitHub
pip3 install git+https://github.com/leoliu5550/QualcommHackathon.git

# Or use pipx for isolated environment (recommended)
brew install pipx
pipx install git+https://github.com/leoliu5550/QualcommHackathon.git
```

### Linux

=== "Ubuntu/Debian"

    ```bash
    # Install Python and pip
    sudo apt update
    sudo apt install python3-pip python3-venv git
    
    # Install FileOrg from GitHub
    pip3 install git+https://github.com/leoliu5550/QualcommHackathon.git
    
    # Or use pipx
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    pipx install git+https://github.com/leoliu5550/QualcommHackathon.git
    
    # Add to PATH if needed
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
    ```

=== "Fedora/RHEL"

    ```bash
    # Install Python and pip
    sudo dnf install python3-pip git
    
    # Install FileOrg from GitHub
    pip3 install git+https://github.com/leoliu5550/QualcommHackathon.git
    ```

=== "Arch Linux"

    ```bash
    # Install Python and pip
    sudo pacman -S python python-pip git
    
    # Install FileOrg from GitHub
    pip install git+https://github.com/leoliu5550/QualcommHackathon.git
    ```

## Hardware Acceleration Setup

### GPU Setup (NVIDIA)

1. **Install CUDA Toolkit**
   ```bash
   # Check CUDA version
   nvidia-smi
   
   # Install appropriate PyTorch
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

2. **Verify GPU Detection**
   ```python
   import torch
   print(f"CUDA Available: {torch.cuda.is_available()}")
   print(f"GPU Count: {torch.cuda.device_count()}")
   print(f"GPU Name: {torch.cuda.get_device_name(0)}")
   ```

### NPU Setup (Snapdragon)

!!! info "Snapdragon X Elite Support"
    NPU support requires Qualcomm AI Stack installation

1. **Install Qualcomm AI Stack**
   - Download from [Qualcomm Developer Network](https://developer.qualcomm.com)
   - Follow platform-specific installation guide

2. **Configure FileOrg for NPU**
   ```python
   # In your config file
   {
     "backend": "qualcomm",
     "dlc_path": "models/tinyllama.dlc"
   }
   ```

## Dependency Management

### Core Dependencies

The default installation includes minimal dependencies:

- `httpx` - NPU API client
- `pypdf>=3.0.0` - PDF parsing
- `python-docx>=0.8.11` - Word document parsing
- `openpyxl>=3.0.0` - Excel file parsing
- `python-pptx>=0.6.21` - PowerPoint parsing
- `tqdm>=4.65.0` - Progress bars
- `charset-normalizer>=3.0.0` - Text encoding detection

### Optional Dependencies

=== "Local Model Support [non-npu]"

    ```bash
    pip install -e ".[non-npu]"
    # Includes:
    # - torch>=2.0.0 - Deep learning framework
    # - transformers>=4.35.0 - Model loading and inference
    # - accelerate>=0.24.0 - Model optimization
    # - sentencepiece>=0.1.99 - Tokenization
    ```

=== "Development [dev]"

    ```bash
    pip install -e ".[dev]"
    # Includes: pytest, black, ruff, mypy, pre-commit
    ```

=== "Documentation [docs]"

    ```bash
    pip install -e ".[docs]"
    # Includes: mkdocs, mkdocs-material
    ```

## Backend Configuration

### NPU Backend (Default)

The default installation uses the Qualcomm NPU API:

```python
# fileorg/ai/config.py
"backend": "qualcomm"  # Uses NPU API at localhost:80
```

### Local Model Backend

For CPU/GPU inference, install with non-npu extras:

```bash
pip install -e ".[non-npu]"
```

Then configure:

```python
# fileorg/ai/config.py
"backend": "local"
"model_id": "iFaz/llama32_3B_en_emo_2000_stp"  # Or any HuggingFace model
```

Models are automatically downloaded on first use to `./fileorg/ai/model/`

## Verification

After installation, verify everything works:

```bash
# Check version
fileorg --version

# Run help
fileorg --help

# Test with sample folder
fileorg --preview ~/Downloads

# Check AI backend
python -c "from fileorg.ai import get_llm, config; print(f'Backend: {config.get(\"backend\")}')"
```

## Troubleshooting

### Common Issues

??? question "ImportError: No module named 'fileorg'"
    
    **Solution**: Ensure installation completed successfully
    ```bash
    # Reinstall from GitHub
    pip uninstall fileorg
    pip install git+https://github.com/leoliu5550/QualcommHackathon.git --no-cache-dir
    ```

??? question "CUDA out of memory" (Local backend only)
    
    **Solution**: Use CPU instead of GPU
    ```python
    # Edit fileorg/ai/config.py
    from fileorg.ai.config import update_default_config
    update_default_config(backend="local", device="cpu")
    ```

??? question "Permission denied on Windows"
    
    **Solution**: Run as Administrator or install in user directory
    ```powershell
    pip install --user git+https://github.com/leoliu5550/QualcommHackathon.git
    ```

??? question "NPU API connection failed" (Qualcomm backend)
    
    **Solution**: Ensure NPU service is running at localhost:80
    ```bash
    # Or switch to local backend
    # Edit fileorg/ai/config.py: "backend": "local"
    # Then install: pip install -e ".[non-npu]"
    ```

## Next Steps

Installation complete! Now you can:

- Read the [Quick Start Guide](quickstart.md)
- Learn about [CLI Usage](../user-guide/cli.md)

## Getting Help

If you encounter issues:

1. Search [GitHub Issues](https://github.com/leoliu5550/QualcommHackathon/issues)
2. Create a new issue with detailed error information