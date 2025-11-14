# E2E Tests for LLM Classifier

This directory contains end-to-end (E2E) tests for the LLM classifier module.

## Test Types

### 1. Mock E2E Tests (`test_two_stage_e2e.py`)
- **Purpose**: Automated E2E tests with mocked LLM responses
- **When to run**: Automatically in CI/CD and pre-commit hooks
- **Dependencies**: No GPU required
- **Execution time**: Fast (~seconds)

### 2. GPU E2E Tests (`test_gpu_real_e2e.py`)
- **Purpose**: Manual validation with real GPU-based LLM inference
- **When to run**: Manual testing before releases
- **Dependencies**: CUDA-capable GPU, torch, transformers
- **Execution time**: Slow (~minutes)
- **Markers**: `@pytest.mark.gpu`, `@pytest.mark.slow`

## Running Tests

### Default Behavior (Excludes GPU Tests)

By default, GPU and slow tests are **excluded** from all test runs:

```bash
# This will NOT run GPU tests
pytest fileorg/llm_classifier/tests/
```

### Running GPU Tests Manually

To run GPU tests, you must explicitly include them:

```bash
# Run all GPU tests
pytest fileorg/llm_classifier/tests/e2e/test_gpu_real_e2e.py -v -s

# Run specific GPU test
pytest fileorg/llm_classifier/tests/e2e/test_gpu_real_e2e.py::TestRealGPUIntegration::test_two_stage_complete_workflow_real -v -s

# Run all tests including GPU and slow tests
pytest fileorg/llm_classifier/tests/ -v -m "gpu or slow"
```

### Skipping GPU Tests

GPU tests will be automatically skipped if:
- GPU is not available (`torch.cuda.is_available() == False`)
- Environment variable `SKIP_GPU_TESTS=1` is set

```bash
# Force skip GPU tests even if GPU is available
SKIP_GPU_TESTS=1 pytest fileorg/llm_classifier/tests/e2e/test_gpu_real_e2e.py
```

## CI/CD and Pre-commit

### What Gets Tested Automatically

- Unit tests
- Integration tests
- Mock E2E tests
- GPU tests (excluded)
- Slow tests (excluded)

### Configuration

The following configuration files ensure GPU tests are excluded:

1. **pyproject.toml**: Default pytest config excludes `gpu` and `slow` markers
2. **.pre-commit-config.yaml**: Pre-commit hook uses `-m "not gpu and not slow"`
3. **.github/workflows/test.yml**: CI/CD workflow uses `-m "not gpu and not slow"`

## GPU Test Coverage

### Test Classes

1. **TestRealGPUIntegration**
   - `test_stage1_keyword_extraction_real`: Validates Stage 1 keyword extraction
   - `test_stage2_classification_real`: Validates Stage 2 classification
   - `test_two_stage_complete_workflow_real`: Full two-stage workflow
   - `test_gpu_device_info`: GPU device information
   - `test_v1_prompts_exist`: Template loading validation

2. **TestPromptQuality**
   - `test_keyword_extraction_quality`: Keyword conciseness and relevance
   - `test_classification_consistency`: Classification consistency

## Requirements for GPU Tests

### Hardware
- NVIDIA GPU with CUDA support
- Minimum 8GB VRAM (for Llama-3.2-3B-Instruct)

### Software
```bash
# Install GPU dependencies
pip install torch transformers accelerate sentencepiece

# Or use poetry/uv with non-npu extras
uv sync --extra non-npu
```

## When to Run GPU Tests

**Run GPU tests when:**
- Implementing new prompt templates
- Modifying prompt builders
- Before major releases
- Performance benchmarking
- Quality assurance with real LLM

**Don't run GPU tests:**
- In CI/CD pipelines (too slow, GPU not available)
- In pre-commit hooks (blocks development workflow)
- During rapid development iterations

## Contributing

When adding new GPU tests:

1. Mark with `@pytest.mark.gpu` and `@pytest.mark.slow`
2. Add to appropriate test class
3. Document expected behavior
4. Ensure tests are skipped gracefully when GPU is unavailable

Example:
```python
@pytest.mark.gpu
@pytest.mark.slow
def test_my_gpu_feature(self, file_classifier):
    """Test description."""
    # Test implementation
```
