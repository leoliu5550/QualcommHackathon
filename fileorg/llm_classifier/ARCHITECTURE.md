# LLM Classifier - Hexagonal Architecture

## Overview

The LLM Classifier has been refactored to follow **Hexagonal Architecture** (also known as Ports and Adapters pattern), providing a clean separation of concerns and adherence to SOLID principles.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     External World                          │
│  (Users, File System, APIs, Databases)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    ADAPTERS (Infrastructure Layer)          │
│  ┌──────────────┬──────────────┬──────────────┬────────┐  │
│  │ LLM Adapters │Config Adapter│Prompt Adapters│Persist.│  │
│  │              │              │               │Adapter │  │
│  │ - Qualcomm   │ - FileConfig │ - Builder     │        │  │
│  │ - Local      │              │ - Validator   │- JSON  │  │
│  └──────────────┴──────────────┴──────────────┴────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ implements
┌─────────────────────────────────────────────────────────────┐
│                      PORTS (Interfaces)                     │
│  ┌─────────────────────┬──────────────────────────────┐   │
│  │ Inbound Ports       │  Outbound Ports              │   │
│  │ (Use Cases)         │  (Dependencies)              │   │
│  │                     │                              │   │
│  │ - ClassifyDocument  │  - LLMPort                   │   │
│  │ - RemapFolders      │  - PromptBuilderPort         │   │
│  │ - ProcessFiles      │  - OutputValidatorPort       │   │
│  │                     │  - ConfigPort                │   │
│  │                     │  - PersistencePort           │   │
│  └─────────────────────┴──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ used by
┌─────────────────────────────────────────────────────────────┐
│            APPLICATION LAYER (Business Logic)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Application Services (Use Case Implementations)      │  │
│  │                                                       │  │
│  │ - DocumentClassificationService                      │  │
│  │ - FolderRemappingService                             │  │
│  │ - FileProcessingService                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   DOMAIN LAYER (Core)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Domain Models (Value Objects & Entities)             │  │
│  │                                                       │  │
│  │ - ClassificationRequest / ClassificationResult       │  │
│  │ - FolderMapping                                      │  │
│  │ - FilePathMapping                                    │  │
│  │ - ProcessingResult                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
fileorg/llm_classifier/
├── ports.py                              # All port definitions (interfaces)
├── run.py                                # Application services & entry point
├── adapters/                             # Infrastructure implementations
│   ├── llm/
│   │   ├── qualcomm_adapter.py          # Qualcomm NPU implementation
│   │   ├── local_adapter.py             # Local transformers implementation
│   │   └── factory.py                   # LLM factory
│   ├── config/
│   │   └── file_config_adapter.py       # File-based configuration
│   ├── prompt/
│   │   ├── builder_adapter.py           # Prompt construction
│   │   └── validator_adapter.py         # Output validation
│   └── persistence/
│       └── json_adapter.py              # JSON storage
├── [legacy folders retained for compatibility]
└── ARCHITECTURE.md                       # This file
```

## Key Principles

### 1. Hexagonal Architecture (Ports & Adapters)

**Ports** define the boundaries and contracts:
- **Inbound Ports**: Entry points for external actors (use cases)
- **Outbound Ports**: Dependencies the application needs (services, repositories)

**Adapters** implement the ports:
- Connect the application to the external world
- Can be easily swapped without changing business logic

### 2. SOLID Principles

#### Single Responsibility Principle (S)
Each class has one reason to change:
- `QualcommLLMAdapter`: Only handles Qualcomm NPU communication
- `PromptBuilderAdapter`: Only constructs prompts
- `DocumentClassificationService`: Only orchestrates classification workflow

#### Open/Closed Principle (O)
Open for extension, closed for modification:
- New LLM backends can be added by creating new adapters
- No need to modify existing code

#### Liskov Substitution Principle (L)
Adapters are interchangeable:
- Any `LLMPort` implementation can replace another
- Application code doesn't know or care which implementation is used

#### Interface Segregation Principle (I)
Focused, minimal interfaces:
- `LLMPort`: Only `generate()` method
- `ConfigPort`: Only configuration retrieval methods
- No fat interfaces with unused methods

#### Dependency Inversion Principle (D)
Depend on abstractions, not concretions:
- Application services depend on `LLMPort`, not `QualcommLLMAdapter`
- Easy to test with mock implementations
- Easy to switch backends

### 3. Dependency Injection

All dependencies are injected through constructors:

```python
# Bad (tight coupling)
class Service:
    def __init__(self):
        self.llm = QualcommLLM()  # Hard dependency!

# Good (dependency injection)
class Service:
    def __init__(self, llm: LLMPort):
        self.llm = llm  # Injected dependency
```

## Usage Examples

### New Architecture (Recommended)

```python
from fileorg.llm_classifier.run import create_classifier_system, run_classification

# Create system with dependency injection
classifier, remapper, processor = create_classifier_system()

# Use individual services
from fileorg.llm_classifier.ports import ClassificationRequest
request = ClassificationRequest(content="Document content here")
result = classifier.classify(request)
print(f"Folder: {result.folder_name}")

# Or use the complete workflow
summaries_data = {
    "summaries": [
        {"summary": "...", "path": "/old/file.txt", "name": "file.txt"}
    ]
}
result = run_classification(summaries_data, base_output_dir="./organized")
```

### Backward Compatibility (Legacy Code)

```python
from fileorg.llm_classifier import get_classifier

# Works exactly like before
classifier = get_classifier()
folder_name = classifier.create_folder_name("Document content here")
```

### Custom Configuration

```python
from fileorg.llm_classifier.adapters.config.file_config_adapter import get_config
from fileorg.llm_classifier.run import create_classifier_system

# Create custom config
config = get_config(preset="advanced")
config.update(backend="local", temperature=0.2)

# Create system with custom config
classifier, remapper, processor = create_classifier_system(config)
```

### Testing with Mocks

```python
from fileorg.llm_classifier.ports import LLMPort
from fileorg.llm_classifier.run import DocumentClassificationService

# Create mock LLM for testing
class MockLLM(LLMPort):
    def generate(self, messages, max_tokens=200):
        return '{"foldername": "TestFolder"}'

# Inject mock into service
mock_llm = MockLLM()
classifier = DocumentClassificationService(mock_llm, prompt_builder, validator)

# Test without real LLM calls
result = classifier.classify(request)
```

## Benefits

### 1. Testability
- Easy to mock dependencies
- Test business logic in isolation
- Fast unit tests without external dependencies

### 2. Maintainability
- Clear separation of concerns
- Easy to understand and modify
- Changes to infrastructure don't affect business logic

### 3. Flexibility
- Swap implementations without code changes
- Support multiple backends simultaneously
- Easy to add new features

### 4. Extensibility
- Add new adapters without modifying existing code
- Support new LLM backends by implementing `LLMPort`
- Add new storage mechanisms by implementing `PersistencePort`

### 5. Backward Compatibility
- Legacy code continues to work
- Gradual migration path
- No breaking changes

## Migration Guide

### For Existing Code

No changes needed! Legacy interfaces are preserved:

```python
# This still works
from fileorg.llm_classifier.classifier.impl import CreateFolderNamer
namer = CreateFolderNamer()
```

### For New Code

Use the new architecture:

```python
# Recommended for new code
from fileorg.llm_classifier.run import create_classifier_system
classifier, remapper, processor = create_classifier_system()
```

## Adding New Features

### Adding a New LLM Backend

1. Create adapter implementing `LLMPort`:

```python
# adapters/llm/cloud_adapter.py
from fileorg.llm_classifier.ports import LLMPort

class CloudLLMAdapter(LLMPort):
    def generate(self, messages, max_tokens=200):
        # Call cloud API
        return response
```

2. Update factory:

```python
# adapters/llm/factory.py
def create_llm(backend, config):
    if backend == "cloud":
        return CloudLLMAdapter(**config)
    # ... existing backends
```

3. Use it:

```python
config = get_config()
config.update(backend="cloud")
classifier, _, _ = create_classifier_system(config)
```

### Adding a New Storage Format

1. Create adapter implementing `PersistencePort`:

```python
# adapters/persistence/yaml_adapter.py
from fileorg.llm_classifier.ports import PersistencePort

class YAMLPersistenceAdapter(PersistencePort):
    def save_result(self, result, output_file):
        # Save as YAML
        pass
```

2. Use it in application services or inject it during creation.

## Troubleshooting

### Import Errors

If you get import errors, ensure all `__init__.py` files are present:
```bash
find fileorg/llm_classifier/adapters -type d -exec touch {}/__init__.py \;
```

### Legacy vs New API

- **Legacy**: Use `from fileorg.llm_classifier.classifier.impl import CreateFolderNamer`
- **New**: Use `from fileorg.llm_classifier.run import create_classifier_system`

Both work and will continue to be supported.

## Further Reading

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection)
- [Ports and Adapters Pattern](https://herbertograca.com/2017/11/16/explicit-architecture-01-ddd-hexagonal-onion-clean-cqrs-how-i-put-it-all-together/)
