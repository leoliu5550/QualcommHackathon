# API Reference

Complete API documentation for FileOrg's Python modules.

## Overview

FileOrg provides a comprehensive Python API for programmatic file organization. All modules are fully documented with type hints and detailed docstrings.

## Core Modules

### Core Components

- [`fileorg.core.organizer`](core/organizer.md) - Main orchestration engine

### AI & Classification

- [`fileorg.ai.interface`](ai/interface.md) - LLM interface and backends

## Quick Examples

### Basic Organization

```python
from fileorg import Organizer

# Initialize organizer
organizer = Organizer()

# Organize a folder
organizer.start_organize("/path/to/folder")
```

### Custom AI Configuration

```python
from fileorg.ai.config import Config
from fileorg.ai.interface import get_llm

# Configure AI backend
config = Config(preset="balanced")
config.update(
    model_id="meta-llama/Llama-3.2-1B",
    temperature=0.1
)

# Get configured LLM
llm = get_llm("local", model_id=config.get("model_id"))
```

### Custom Parser

```python
from fileorg.parsers.base import BaseParser, ParseResult
from pathlib import Path

class CustomParser(BaseParser):
    def parse(self, file_path: Path) -> ParseResult:
        # Your parsing logic
        return ParseResult(
            success=True,
            content="Extracted content",
            file_type="custom"
        )
```

## Module Structure

```
fileorg/
├── core/           # Core orchestration
│   └── organizer.py
├── ai/             # AI integration
│   ├── interface.py
│   ├── config.py
│   └── pipeline.py
├── classifier/     # Classification logic
│   ├── classifier.py
│   └── prompt_engine/
├── parsers/        # File parsers
│   ├── base.py
│   └── [format]_parser.py
├── scanner/        # File scanning
│   ├── core.py
│   └── helpers.py
├── reporter/       # Report generation
│   ├── generator.py
│   └── visualizer.py
└── restore/        # Restoration logic
    └── restore_folder.py
```

## Type Hints

All FileOrg modules use comprehensive type hints:

```python
from typing import List, Dict, Optional
from pathlib import Path

def organize_files(
    path: Path,
    preview: bool = False,
    output_dir: Optional[Path] = None
) -> Dict[str, List[str]]:
    """Organize files with type safety."""
    ...
```

## Error Handling

FileOrg uses custom exceptions for clear error handling:

```python
from fileorg.exceptions import (
    FileOrgError,
    ParseError,
    ClassificationError,
    RestoreError
)

try:
    organizer.start_organize(path)
except FileOrgError as e:
    print(f"Organization failed: {e}")
```

## Async Support

Some operations support async execution:

```python
import asyncio
from fileorg.scanner import AsyncFileScanner

async def scan_large_directory():
    scanner = AsyncFileScanner("/large/directory")
    results = await scanner.scan_async()
    return results

# Run async scan
results = asyncio.run(scan_large_directory())
```

## Best Practices

1. **Use Type Hints**: All functions should have proper type annotations
2. **Handle Errors**: Use try-except blocks for robust error handling
3. **Configure Logging**: Set up logging for debugging
4. **Resource Management**: Use context managers for file operations
5. **Test Your Code**: Write unit tests for custom components

## API Stability

| Module | Stability | Notes |
|--------|-----------|-------|
| `core.organizer` | Stable | Core API, backward compatible |
| `ai.interface` | Stable | Extensible for new backends |
| `parsers.base` | Stable | Interface won't change |
| `classifier` | Beta | May have minor changes |

## Getting Help

- Check module docstrings for detailed information
- Report issues on [GitHub](https://github.com/leoliu5550/QualcommHackathon/issues)