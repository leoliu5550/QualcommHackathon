# Installation Guide

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 500MB for installation + space for models
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+

### Recommended Requirements
- **GPU**: NVIDIA GPU with CUDA support (optional)
- **NPU**: Qualcomm Snapdragon X Elite (optional)
- **RAM**: 16GB for optimal performance
- **Storage**: 2GB for models and cache

## Installation Methods

### Method 1: Install from PyPI (Recommended)

=== "Standard Installation"

    ```bash
    # Install FileOrg
    pip install fileorg
    
    # Verify installation
    fileorg --version
    ```

=== "With GPU Support"

    ```bash
    # Install with CUDA support
    pip install fileorg[gpu]
    
    # Verify CUDA
    python -c "import torch; print(torch.cuda.is_available())"
    ```

=== "With NPU Support"

    ```bash
    # Install with Snapdragon NPU support
    pip install fileorg[npu]
    
    # Additional NPU setup required
    # See NPU Integration guide
    ```

### Method 2: Install from GitHub

```bash
# Clone repository
git clone https://github.com/leoliu5550/QualcommHackathon.git
cd QualcommHackathon

# Install in development mode
pip install -e .

# Or install directly via pipx
pipx install git+https://github.com/leoliu5550/QualcommHackathon.git
```

### Method 3: Windows Installer

For Windows users, we provide a convenient installer with right-click integration:

1. Download the installer from [Releases](https://github.com/leoliu5550/QualcommHackathon/releases)
2. Run `fileorg_installer.exe`
3. FileOrg will be added to your right-click context menu

## Platform-Specific Instructions

### Windows

#### Using pip

```powershell
# Open PowerShell as Administrator
python -m pip install --upgrade pip
pip install fileorg

# Add to PATH if needed
$env:Path += ";$env:USERPROFILE\.local\bin"
```

#### Right-Click Integration

After installation, register the context menu:

```powershell
# Run as Administrator
fileorg --register-context-menu
```

Now you can right-click any folder and select "Organize with FileOrg"

### macOS

```bash
# Install via Homebrew (if available)
brew install python@3.11
pip3 install fileorg

# Or use pipx for isolated environment
brew install pipx
pipx install fileorg
```

### Linux

=== "Ubuntu/Debian"

    ```bash
    # Install Python and pip
    sudo apt update
    sudo apt install python3-pip python3-venv
    
    # Install FileOrg
    pip3 install fileorg
    
    # Add to PATH
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
    ```

=== "Fedora/RHEL"

    ```bash
    # Install Python and pip
    sudo dnf install python3-pip
    
    # Install FileOrg
    pip3 install fileorg
    ```

=== "Arch Linux"

    ```bash
    # Install Python and pip
    sudo pacman -S python python-pip
    
    # Install FileOrg
    pip install fileorg
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

FileOrg automatically installs these dependencies:

- `transformers>=4.35.0` - Model loading and inference
- `torch>=2.0.0` - Deep learning framework
- `pypdf>=3.17.0` - PDF parsing
- `python-docx>=1.0.0` - Word document parsing
- `openpyxl>=3.1.0` - Excel file parsing
- `python-pptx>=0.6.0` - PowerPoint parsing

### Optional Dependencies

=== "Development"

    ```bash
    pip install fileorg[dev]
    # Includes: pytest, black, flake8, mypy
    ```

=== "Documentation"

    ```bash
    pip install fileorg[docs]
    # Includes: mkdocs, mkdocs-material
    ```

=== "All Extras"

    ```bash
    pip install fileorg[all]
    # Includes all optional dependencies
    ```

## Model Installation

FileOrg automatically downloads required models on first use:

### Default Model (TinyLlama)

- **Size**: ~500MB
- **Location**: `~/.cache/huggingface/`
- **Auto-download**: Yes

### Alternative Models

```python
# Configure custom model
from fileorg.ai.config import update_default_config

update_default_config(
    model_id="meta-llama/Llama-3.2-1B",
    backend="local"
)
```

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
python -c "from fileorg.ai import get_llm; print(get_llm('local'))"
```

## Troubleshooting

### Common Issues

??? question "ImportError: No module named 'fileorg'"
    
    **Solution**: Ensure pip installation completed successfully
    ```bash
    pip uninstall fileorg
    pip install fileorg --no-cache-dir
    ```

??? question "CUDA out of memory"
    
    **Solution**: Use smaller model or reduce batch size
    ```python
    # Use CPU instead
    update_default_config(device="cpu")
    ```

??? question "Permission denied on Windows"
    
    **Solution**: Run as Administrator or install in user directory
    ```powershell
    pip install --user fileorg
    ```

??? question "Model download fails"
    
    **Solution**: Check internet connection or manually download
    ```bash
    # Manual download
    huggingface-cli download iFaz/llama32_3B_en_emo_2000_stp
    ```

## Next Steps

Installation complete! Now you can:

- Read the [Quick Start Guide](quickstart.md)
- Learn about [CLI Usage](../user-guide/cli.md)

## Getting Help

If you encounter issues:

1. Search [GitHub Issues](https://github.com/leoliu5550/QualcommHackathon/issues)
2. Create a new issue with detailed error information