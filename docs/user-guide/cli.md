# Command Line Interface

## Overview

FileOrg provides a powerful command-line interface for all file organization tasks.

## Basic Usage

```bash
fileorg [OPTIONS] TARGET_PATH
```

## Commands

### Main Command

```bash
fileorg <path>
```
Organizes files in the specified directory.

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--preview` | `-p` | Preview organization without moving files |
| `--restore` | `-r` | Restore files to original locations |
| `--output` | `-o` | Specify output directory |
| `--help` | `-h` | Show help message |
| `--version` | `-v` | Show version |

## Examples

### Basic Organization

```bash
# Organize Downloads folder
fileorg ~/Downloads

# Preview first
fileorg ~/Downloads --preview

# Custom output directory
fileorg ~/Downloads --output ~/Organized
```

### Restore Operations

```bash
# Restore to original structure
fileorg ~/Downloads --restore
```

### GUI Mode

```bash
# Launch interactive GUI
fileorg start
```

## Advanced Options

### Model Configuration

```bash
# Use specific model
fileorg ~/Documents --model "TinyLlama/TinyLlama-1.1B"

# Force CPU mode
fileorg ~/Documents --device cpu

# Use NPU acceleration
fileorg ~/Documents --backend qualcomm
```

### Processing Options

```bash
# Limit file types
fileorg ~/Downloads --types "pdf,docx,txt"

# Set maximum files
fileorg ~/Downloads --max-files 100

# Exclude patterns
fileorg ~/Downloads --exclude "*.tmp,*.log"
```

### Output Control

```bash
# Verbose output
fileorg ~/Downloads --verbose

# Quiet mode
fileorg ~/Downloads --quiet

# JSON output
fileorg ~/Downloads --json
```

## Configuration File

Create `~/.fileorg/config.json`:

```json
{
  "backend": "local",
  "model_id": "iFaz/llama32_3B_en_emo_2000_stp",
  "temperature": 0.1,
  "use_few_shot": true,
  "device": "cuda"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FILEORG_CONFIG` | Config file path | `~/.fileorg/config.json` |
| `FILEORG_CACHE` | Cache directory | `~/.cache/fileorg` |
| `FILEORG_MODEL_PATH` | Model storage | `~/.cache/huggingface` |
| `FILEORG_LOG_LEVEL` | Logging level | `INFO` |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Path not found |
| 4 | Permission denied |
| 5 | Restore failed |

## Batch Processing

### Using Shell Scripts

```bash
#!/bin/bash
# organize_all.sh

folders=(
    "$HOME/Downloads"
    "$HOME/Desktop"
    "$HOME/Documents"
)

for folder in "${folders[@]}"; do
    echo "Organizing $folder..."
    fileorg "$folder" --preview
    
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        fileorg "$folder"
    fi
done
```

### Using Python

```python
import subprocess
from pathlib import Path

folders = [
    Path.home() / "Downloads",
    Path.home() / "Desktop",
]

for folder in folders:
    # Preview
    subprocess.run(["fileorg", str(folder), "--preview"])
    
    # Organize
    if input(f"Organize {folder}? (y/n): ").lower() == 'y':
        subprocess.run(["fileorg", str(folder)])
```

## Integration

### Shell Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Quick organize downloads
alias orgdl='fileorg ~/Downloads'

# Preview organization
alias orgp='fileorg --preview'

# Restore last organization
alias orgr='fileorg --restore'
```

### Cron Jobs

```bash
# Weekly organization of Downloads
0 0 * * 0 fileorg ~/Downloads --quiet

# Daily cleanup of Desktop
0 20 * * * fileorg ~/Desktop --preview | mail -s "Desktop Organization" user@example.com
```

## Tips & Tricks

1. **Always preview first** - Use `--preview` before organizing important folders
2. **Start small** - Test on a small folder before large directories
3. **Check reports** - Review generated reports for insights
4. **Use verbose mode** - Add `--verbose` when debugging
5. **Custom models** - Try different models for better categorization

## Common Issues

### Permission Errors

```bash
# Run with elevated permissions if needed
sudo fileorg /system/folder

# Or change ownership
chown -R $USER:$USER /path/to/folder
```

### Memory Issues

```bash
# Use smaller model
fileorg ~/LargeFolder --model "TinyLlama/TinyLlama-1.1B"

# Process in batches
fileorg ~/LargeFolder --max-files 50
```

### Slow Performance

```bash
# Enable GPU
fileorg ~/Documents --device cuda

# Use faster model
fileorg ~/Documents --model "iFaz/llama32_3B_en_emo_2000_stp"
```