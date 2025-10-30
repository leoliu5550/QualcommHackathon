# AI Inference & Deployment Guide

**Version**: 2.0.0
**Last Updated**: 2025-10-26
**Module**: `fileorg.llm_classifier`

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Reference](#module-reference)
3. [API Documentation](#api-documentation)
4. [Extension Guide](#extension-guide)
5. [Deployment Instructions](#deployment-instructions)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Module Structure

The `fileorg.llm_classifier` module provides a unified, modular architecture for AI-powered document classification and organization. All AI inference and deployment functionality has been consolidated into this single package for better maintainability and extensibility.

```
fileorg/llm_classifier/
├── __init__.py                      # Main module exports
├── AI_INFERENCE_GUIDE.md            # This documentation
│
├── llm/                             # LLM Inference Module
│   ├── __init__.py
│   ├── interface.py                 # BaseLLM abstract class
│   ├── impl.py                      # QualcommLLM, LocalTransformersLLM
│   └── factory.py                   # get_llm() factory function
│
├── classifier/                      # Document Classification Module
│   ├── __init__.py
│   ├── interface.py                 # BaseClassifier protocol
│   ├── impl.py                      # CreateFolderNamer implementation
│   └── legacy.py                    # V1 classifier (legacy)
│
├── prompt/                          # Prompt Engineering Module
│   ├── __init__.py
│   ├── interface.py                 # Prompt builder protocols
│   ├── builder.py                   # Prompt construction
│   ├── templates.py                 # v1/v2 templates
│   ├── optimizer.py                 # Output optimization
│   └── examples.py                  # Few-shot examples
│
├── config/                          # Configuration Management Module
│   ├── __init__.py
│   ├── interface.py                 # Config dataclasses
│   └── impl.py                      # Configuration implementation
│
├── pipeline/                        # Deployment Pipeline Module
│   ├── __init__.py
│   ├── interface.py                 # Pipeline protocols
│   └── impl.py                      # ONNX/Qualcomm deployment
│
└── utils/                           # Shared Utilities
    ├── __init__.py
    └── helpers.py                   # Common helper functions
```

### Design Principles

1. **Separation of Concerns**: Each module has a clear, single responsibility
2. **Interface-Implementation Pattern**: All modules separate abstract interfaces from concrete implementations
3. **Factory Pattern**: LLM backends are created through factory functions for easy switching
4. **Configuration-Driven**: Behavior is controlled through centralized configuration
5. **Extensibility**: New backends, prompts, or classifiers can be added without modifying existing code

### Data Flow

```
User Input
    ↓
[Scanner] → File Paths
    ↓
[Parser] → Document Content
    ↓
[Config] → Load Configuration
    ↓
[LLM Factory] → Create LLM Backend
    ↓
[Prompt Builder] → Construct Optimized Prompts
    ↓
[LLM Inference] → Generate Classifications
    ↓
[Prompt Optimizer] → Validate & Clean Outputs
    ↓
[Classifier] → Folder Mappings
    ↓
[Organizer] → File Movements
    ↓
[Reporter] → Final Reports
```

---

## Module Reference

### 1. LLM Module (`fileorg.llm_classifier.llm`)

**Purpose**: Provides abstract interfaces and concrete implementations for LLM inference.

**Key Components**:
- `BaseLLM`: Abstract base class defining the inference interface
- `QualcommLLM`: Qualcomm Snapdragon NPU implementation
- `LocalTransformersLLM`: Local CPU/GPU implementation using Hugging Face transformers
- `get_llm()`: Factory function for creating LLM instances

**File Locations**:
- Interface: `fileorg/llm_classifier/llm/interface.py`
- Implementation: `fileorg/llm_classifier/llm/impl.py`
- Factory: `fileorg/llm_classifier/llm/factory.py`

### 2. Classifier Module (`fileorg.llm_classifier.classifier`)

**Purpose**: Provides document classification and folder naming capabilities.

**Key Components**:
- `BaseClassifier`: Abstract base class for classifiers
- `CreateFolderNamer`: Enhanced v2 classifier with prompt engineering
- `CreateFolderNamerV1`: Legacy v1 classifier (backward compatibility)

**File Locations**:
- Interface: `fileorg/llm_classifier/classifier/interface.py`
- Implementation: `fileorg/llm_classifier/classifier/impl.py`
- Legacy: `fileorg/llm_classifier/classifier/legacy.py`

### 3. Prompt Module (`fileorg.llm_classifier.prompt`)

**Purpose**: Provides prompt engineering, templates, and output optimization.

**Key Components**:
- `PromptBuilder`: Constructs optimized prompts with few-shot examples
- `PromptTemplates`: Manages v1 and v2 prompt templates
- `PromptOptimizer`: Validates and optimizes LLM outputs
- `FewShotExamples`: Provides curated examples for few-shot learning

**File Locations**:
- Interface: `fileorg/llm_classifier/prompt/interface.py`
- Builder: `fileorg/llm_classifier/prompt/builder.py`
- Templates: `fileorg/llm_classifier/prompt/templates.py`
- Optimizer: `fileorg/llm_classifier/prompt/optimizer.py`
- Examples: `fileorg/llm_classifier/prompt/examples.py`

### 4. Config Module (`fileorg.llm_classifier.config`)

**Purpose**: Manages configuration for LLM backends and prompt engineering.

**Key Components**:
- `LLMConfig`: Dataclass for LLM backend configuration
- `PromptConfig`: Dataclass for prompt engineering configuration
- `AIConfig`: Combined configuration class
- `get_config()`: Factory function for configuration instances

**File Locations**:
- Interface: `fileorg/llm_classifier/config/interface.py`
- Implementation: `fileorg/llm_classifier/config/impl.py`

### 5. Pipeline Module (`fileorg.llm_classifier.pipeline`)

**Purpose**: Provides model deployment and optimization pipelines.

**Key Components**:
- `ModelPipeline`: Abstract base class for deployment pipelines
- `QualcommPipeline`: Qualcomm NPU deployment pipeline (placeholder)
- `LocalPipeline`: Local CPU/GPU deployment pipeline

**File Locations**:
- Interface: `fileorg/llm_classifier/pipeline/interface.py`
- Implementation: `fileorg/llm_classifier/pipeline/impl.py`

---

## API Documentation

### Quick Start

```python
from fileorg.llm_classifier import get_llm, get_config, get_classifier

# 1. Get configuration
config = get_config("balanced")  # Options: "legacy", "balanced", "advanced"

# 2. Create LLM backend
llm = get_llm(config.get("backend"))  # Automatically uses config settings

# 3. Create classifier
classifier = get_classifier(
    use_advanced_prompt=True,
    prompt_version="v2",
    use_few_shot=True,
    use_domain_detection=False
)

# 4. Classify document
document_content = "Chapter 4: Principal Component Analysis..."
folder_name = classifier.create_folder_name(document_content)
print(f"Classified as: {folder_name}")  # Output: "Academic/Statistics"
```

### LLM API

#### Creating LLM Instances

```python
from fileorg.llm_classifier.llm import get_llm

# Qualcomm NPU Backend
llm = get_llm(
    backend="qualcomm",
    api_key="your-api-key",  # Or set QUALCOMM_API_KEY env var
    api_url="http://127.0.0.1:80/v1.0/chat/completions",
    model=".bot/Llama 3.1 8B @NPU",
    timeout=600.0
)

# Local Transformers Backend
llm = get_llm(
    backend="local",
    model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    device="cuda",  # or "cpu"
    cache_dir="./models"
)

# Perform inference
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Classify this document..."},
]
response = llm.inference(messages, max_new_tokens=200)
```

### Classifier API

#### Basic Classification

```python
from fileorg.llm_classifier.classifier import CreateFolderNamer

# Create classifier with default settings
classifier = CreateFolderNamer()

# Classify single document
folder = classifier.create_folder_name("Document content here...")

# Group similar folders
folders = ["Statistics", "Mathematics", "DataAnalysis"]
mappings = classifier.remapping_folder(folders)
# Returns: [{"foldername": "Statistics", "groupname": "Academic"}, ...]
```

#### Advanced Classification with Prompt Engineering

```python
from fileorg.llm_classifier.classifier import CreateFolderNamer

# Create classifier with advanced features
classifier = CreateFolderNamer(
    use_advanced_prompt=True,
    prompt_version="v2",
    use_few_shot=True,
    use_domain_detection=True
)

# Process multiple files
summaries_data = {
    "summaries": [
        {
            "summary": "Statistical analysis of data...",
            "path": "/path/to/file1.pdf",
            "name": "stats.pdf"
        },
        {
            "summary": "Business order document...",
            "path": "/path/to/file2.docx",
            "name": "order.docx"
        }
    ]
}

result = classifier.process_files(summaries_data, base_output_dir="./organized/")
# Returns: {"file_paths": [{"original": "...", "new": "..."}, ...]}
```

### Configuration API

#### Using Configuration Presets

```python
from fileorg.llm_classifier.config import get_config, get_preset_config

# Get config with preset
config = get_preset_config("balanced")  # Options: "legacy", "balanced", "advanced"

# Access configuration values
backend = config.get("backend")  # "qualcomm"
use_few_shot = config.get("use_few_shot")  # True
temperature = config.get("temperature")  # 0.1

# Update configuration
config.update(temperature=0.2, max_new_tokens=300)

# Get all config as dictionary
all_config = config.get_all()
```

#### Custom Configuration

```python
from fileorg.llm_classifier.config import get_config

# Create custom configuration
config = get_config(
    backend="qualcomm",
    prompt_version="v2",
    use_few_shot=True,
    use_domain_detection=True,
    temperature=0.15,
    max_new_tokens=250
)
```

### Prompt Engineering API

#### Building Custom Prompts

```python
from fileorg.llm_classifier.prompt import PromptBuilder

# Create prompt builder
builder = PromptBuilder(
    version="v2",
    use_few_shot=True,
    use_domain_detection=True
)

# Build classification prompt
messages = builder.build_classification_prompt(
    content="Chapter 4: Statistical Analysis...",
    max_content_length=500
)

# Build remapping prompt
folders = ["Statistics", "Mathematics", "DataAnalysis"]
messages = builder.build_remapping_prompt(folders)
```

#### Using Prompt Optimizer

```python
from fileorg.llm_classifier.prompt import PromptOptimizer

# Create optimizer
optimizer = PromptOptimizer()

# Optimize content
optimized = optimizer.optimize_content(
    content="Long document content...",
    max_length=500
)

# Validate LLM output
raw_output = '{"foldername": "Statistics"}'
is_valid, fixed_output = optimizer.validate_output(raw_output, expected_format="json")

# Get optimization statistics
stats = optimizer.get_optimization_stats()
print(f"Total optimizations: {stats['total_optimized']}")
```

---

## Extension Guide

### Adding a New LLM Backend

To add support for a new LLM backend (e.g., OpenAI, Anthropic, custom API):

1. **Create implementation class** in `fileorg/llm_classifier/llm/impl.py`:

```python
class OpenAILLM(BaseLLM):
    """OpenAI API backend implementation."""

    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        self.api_key = api_key
        self.model = model
        # Initialize OpenAI client

    def inference(self, prompt: str, max_new_tokens: int = 128) -> str:
        # Implement OpenAI API call
        # Convert prompt format if needed
        # Return generated text
        pass
```

2. **Update factory function** in `fileorg/llm_classifier/llm/factory.py`:

```python
def get_llm(backend: str = "qualcomm", **kwargs) -> BaseLLM:
    if backend == "local":
        return LocalTransformersLLM(**kwargs)
    elif backend == "qualcomm":
        return QualcommLLM(**kwargs)
    elif backend == "openai":
        return OpenAILLM(**kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")
```

3. **Update exports** in `fileorg/llm_classifier/llm/__init__.py`:

```python
from fileorg.llm_classifier.llm.impl import QualcommLLM, LocalTransformersLLM, OpenAILLM

__all__ = ["BaseLLM", "get_llm", "QualcommLLM", "LocalTransformersLLM", "OpenAILLM"]
```

### Adding Custom Prompt Templates

To add new prompt templates for specialized domains:

1. **Define template** in `fileorg/llm_classifier/prompt/templates.py`:

```python
class PromptTemplates:
    # Add your custom template
    MEDICAL_TEMPLATE = {
        "system": "You are a medical document classification expert...",
        "prompt_prefix": "Classify this medical document: ",
        "assistant_prefix": '{"foldername": "'
    }

    @classmethod
    def get_template(cls, version: str = "v2", template_type: str = "classification"):
        # Add handling for your template
        if template_type == "medical":
            return cls.MEDICAL_TEMPLATE
        # ... existing code
```

2. **Add domain detection** (optional):

```python
@classmethod
def detect_domain(cls, content: str) -> str:
    content_lower = content.lower()

    # Add medical domain detection
    medical_keywords = ["patient", "diagnosis", "treatment", "medical", "clinical"]
    if any(keyword in content_lower for keyword in medical_keywords):
        return "Medical"

    # ... existing code
```

### Creating a Custom Classifier

To create a specialized classifier with custom logic:

1. **Implement BaseClassifier** in a new file:

```python
from fileorg.llm_classifier.classifier.interface import BaseClassifier
from fileorg.llm_classifier.llm import get_llm
from typing import List, Dict, Any

class CustomClassifier(BaseClassifier):
    """Custom classifier with specialized logic."""

    def __init__(self, **kwargs):
        self.llm = get_llm(**kwargs)
        # Custom initialization

    def create_folder_name(self, content: str) -> str:
        # Custom classification logic
        pass

    def remapping_folder(self, candidate_folder: List[str]) -> List[Dict[str, str]]:
        # Custom grouping logic
        pass

    def process_files(self, summaries_data: Dict[str, Any], base_output_dir: str) -> Dict[str, List[Dict[str, str]]]:
        # Custom file processing logic
        pass
```

2. **Register classifier** (if needed):

```python
from fileorg.llm_classifier.classifier import CreateFolderNamer, CustomClassifier

def get_classifier(classifier_type: str = "default", **kwargs):
    if classifier_type == "default":
        return CreateFolderNamer(**kwargs)
    elif classifier_type == "custom":
        return CustomClassifier(**kwargs)
    else:
        raise ValueError(f"Unknown classifier type: {classifier_type}")
```

---

## Deployment Instructions

### Environment Setup

#### Required Dependencies

**Core Dependencies** (always required):
```bash
pip install httpx python-docx openpyxl python-pptx pypdf tqdm charset-normalizer
```

**Optional Dependencies**:
```bash
# For local GPU/CPU inference
pip install torch transformers accelerate sentencepiece

# For development
pip install pytest pytest-cov black ruff mypy

# For documentation
pip install mkdocs mkdocs-material
```

#### Environment Variables

**Required for Qualcomm NPU Backend**:
```bash
# Windows
set QUALCOMM_API_KEY=your-api-key-here

# Linux/Mac
export QUALCOMM_API_KEY=your-api-key-here
```

**Optional Configuration**:
```bash
# Model cache directory
export TRANSFORMERS_CACHE=/path/to/cache

# Logging level
export LOG_LEVEL=INFO
```

### Qualcomm NPU Deployment

#### Prerequisites
- Qualcomm Snapdragon X series laptop
- NPU inference service running at `http://127.0.0.1:80`
- Valid API authentication key

#### Configuration

```python
from fileorg.llm_classifier.config import get_config

# Create Qualcomm-optimized configuration
config = get_config(
    backend="qualcomm",
    api_key="your-api-key",  # Or use QUALCOMM_API_KEY env var
    api_url="http://127.0.0.1:80/v1.0/chat/completions",
    model=".bot/Llama 3.1 8B @NPU",
    timeout=600.0,
    prompt_version="v2",
    use_few_shot=True,
    temperature=0.1
)
```

#### Performance Optimization

1. **Batch Processing**: Process multiple files before calling LLM
2. **Content Truncation**: Limit content to 500 characters for efficiency
3. **Prompt Optimization**: Use v2 prompts with domain detection
4. **Connection Pooling**: Reuse HTTP connections (automatic with `httpx.Client`)

### Local Deployment (CPU/GPU)

#### Prerequisites
- Python 3.8+
- CUDA 11.8+ (for GPU acceleration)
- 8GB+ RAM (16GB+ recommended)

#### Configuration

```python
from fileorg.llm_classifier.config import get_config

# Create local configuration
config = get_config(
    backend="local",
    model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    device="cuda",  # or "cpu"
    cache_dir="./models",
    prompt_version="v2",
    use_few_shot=True
)
```

#### First-Time Setup

```python
from fileorg.llm_classifier.llm import get_llm

# First run will download model (1-2GB)
llm = get_llm(
    backend="local",
    model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    device="cuda",
    cache_dir="./models"
)

print("Model loaded successfully!")
```

### Production Deployment Checklist

- [ ] Set `QUALCOMM_API_KEY` environment variable
- [ ] Configure logging and monitoring
- [ ] Set up error handling and retries
- [ ] Test with sample documents
- [ ] Benchmark inference latency
- [ ] Configure backup/fallback models
- [ ] Document custom configuration
- [ ] Set up health checks
- [ ] Configure resource limits
- [ ] Test failure scenarios

---

## Best Practices

### Security

1. **Never hardcode API keys** - Always use environment variables:
   ```python
   import os
   api_key = os.getenv("QUALCOMM_API_KEY")
   if not api_key:
       raise ValueError("QUALCOMM_API_KEY environment variable not set")
   ```

2. **Validate all inputs** - Sanitize user-provided content:
   ```python
   def validate_content(content: str) -> str:
       if not content or len(content) > 10000:
           raise ValueError("Invalid content length")
       return content.strip()
   ```

3. **Use secure connections** - Always use HTTPS for remote APIs

4. **Implement rate limiting** - Prevent abuse and control costs

### Performance

1. **Use Configuration Presets**:
   - `"legacy"`: Fastest, basic classification
   - `"balanced"`: Recommended, good accuracy with reasonable speed
   - `"advanced"`: Best accuracy, slower (use for important documents)

2. **Optimize Content Length**:
   ```python
   # Truncate long documents
   content = document_content[:500]  # First 500 characters usually sufficient
   ```

3. **Batch Similar Operations**:
   ```python
   # Process multiple files before inference
   folders = [classifier.create_folder_name(doc) for doc in documents]
   # Then batch the remapping
   mappings = classifier.remapping_folder(folders)
   ```

4. **Cache Results**:
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=1000)
   def cached_classify(content_hash: str) -> str:
       return classifier.create_folder_name(content)
   ```

### Error Handling

1. **Graceful Degradation**:
   ```python
   try:
       llm = get_llm("qualcomm")
   except Exception as e:
       logger.warning(f"Qualcomm backend failed: {e}, falling back to local")
       llm = get_llm("local")
   ```

2. **Timeout Handling**:
   ```python
   llm = get_llm("qualcomm", timeout=30.0)  # 30 second timeout
   ```

3. **Validation and Fallback**:
   ```python
   result = llm.inference(prompt)
   is_valid, fixed = optimizer.validate_output(result)
   if not is_valid:
       logger.error("Invalid output, using default category")
       return "Uncategorized/Misc"
   return fixed
   ```

### Code Organization

1. **Use Factory Functions**:
   ```python
   # Good
   llm = get_llm("qualcomm")

   # Avoid
   llm = QualcommLLM(api_key="...", api_url="...", ...)
   ```

2. **Leverage Configuration**:
   ```python
   # Good
   config = get_config("balanced")
   classifier = CreateFolderNamer(
       use_advanced_prompt=config.get("use_advanced_prompt"),
       prompt_version=config.get("prompt_version"),
       use_few_shot=config.get("use_few_shot")
   )

   # Better
   from fileorg.llm_classifier.classifier import get_create_name
   classifier = get_create_name()  # Uses default config
   ```

3. **Separate Concerns**:
   ```python
   # Good - each module handles its own concern
   llm = get_llm()
   builder = PromptBuilder()
   optimizer = PromptOptimizer()

   messages = builder.build_classification_prompt(content)
   result = llm.inference(messages)
   is_valid, fixed = optimizer.validate_output(result)
   ```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**:
```
ImportError: cannot import name 'create_name' from 'fileorg.classifier'
```

**Solution**:
```python
# Old import (deprecated)
from fileorg.classifier.classifier import create_name

# New import (correct)
from fileorg.llm_classifier.classifier.impl import create_name
```

#### 2. API Authentication Failures

**Problem**:
```
ValueError: Qualcomm API key must be provided
```

**Solution**:
```bash
# Set environment variable
export QUALCOMM_API_KEY=your-api-key-here

# Or provide in code (not recommended for production)
llm = get_llm("qualcomm", api_key="your-api-key")
```

#### 3. Connection Timeout

**Problem**:
```
httpx.ReadTimeout: Request timeout after 600.0 seconds
```

**Solution**:
```python
# Increase timeout
llm = get_llm("qualcomm", timeout=1200.0)  # 20 minutes

# Or reduce content length
content = document[:300]  # Shorter content = faster inference
```

#### 4. JSON Parsing Errors

**Problem**:
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Solution**:
```python
# Use output validation
from fileorg.llm_classifier.prompt import PromptOptimizer

optimizer = PromptOptimizer()
raw_output = llm.inference(prompt)
is_valid, fixed_output = optimizer.validate_output(raw_output, "json")

if is_valid:
    data = json.loads(fixed_output)
else:
    # Fallback logic
    data = {"foldername": "Uncategorized"}
```

#### 5. Out of Memory (Local Backend)

**Problem**:
```
RuntimeError: CUDA out of memory
```

**Solution**:
```python
# Use smaller model
llm = get_llm("local", model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0")

# Or use CPU
llm = get_llm("local", device="cpu")

# Or enable quantization (if supported)
llm = get_llm("local", load_in_8bit=True)
```

### Debugging Tips

1. **Enable verbose logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Test with simple examples**:
   ```python
   # Minimal test
   from fileorg.llm_classifier.llm import get_llm

   llm = get_llm("qualcomm")
   result = llm.inference([
       {"role": "user", "content": "Hello, world!"}
   ])
   print(result)
   ```

3. **Check module versions**:
   ```python
   from fileorg import llm_classifier
   print(llm_classifier.__version__)  # Should be 2.0.0
   ```

4. **Inspect prompts**:
   ```python
   from fileorg.llm_classifier.prompt import PromptBuilder

   builder = PromptBuilder(version="v2")
   messages = builder.build_classification_prompt("test content")

   # Print constructed prompt
   import json
   print(json.dumps(messages, indent=2))
   ```

### Getting Help

- **Documentation**: Read this guide thoroughly
- **Examples**: Check `examples/` directory for sample code
- **Issues**: Report bugs at [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: Ask questions at [GitHub Discussions](https://github.com/your-repo/discussions)

---

## Appendix

### Configuration Reference

#### LLM Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | str | `"qualcomm"` | LLM backend ("qualcomm" or "local") |
| `model_id` | str | `"iFaz/llama32_3B_en_emo_2000_stp"` | Hugging Face model ID |
| `api_key` | str | `None` | API authentication key |
| `api_url` | str | `"http://127.0.0.1:80/v1.0/chat/completions"` | NPU API endpoint |
| `model` | str | `".bot/Llama 3.1 8B @NPU"` | Model name for API |
| `timeout` | float | `600.0` | Request timeout (seconds) |
| `device` | str | `"cuda"` | Device for local inference |
| `cache_dir` | str | `"./fileorg/llm_classifier/llm/model"` | Model cache directory |

#### Prompt Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `classifier_version` | str | `"v2"` | Classifier version ("v1" or "v2") |
| `enable_v2_features` | bool | `True` | Enable v2 features globally |
| `prompt_version` | str | `"v2"` | Prompt template version |
| `use_advanced_prompt` | bool | `True` | Use advanced prompting |
| `use_few_shot` | bool | `True` | Include few-shot examples |
| `few_shot_count` | int | `2` | Number of examples |
| `use_domain_detection` | bool | `False` | Enable domain detection |
| `optimize_content` | bool | `False` | Enable content optimization |
| `max_content_length` | int | `500` | Maximum content length |
| `validate_output` | bool | `False` | Enable output validation |
| `temperature` | float | `0.1` | LLM sampling temperature |
| `max_new_tokens` | int | `200` | Maximum tokens to generate |

### Version History

- **v2.0.0** (2025-10-26): Major refactoring into modular architecture
  - Consolidated all AI code into `llm_classifier` module
  - Separated interfaces from implementations
  - Added comprehensive documentation
  - Improved configuration management
  - Enhanced prompt engineering capabilities

- **v1.0.0** (Previous): Initial implementation
  - Basic LLM inference
  - Simple classification
  - Legacy prompt templates

---

**End of AI Inference & Deployment Guide**

For the latest updates and additional resources, visit the project repository.
