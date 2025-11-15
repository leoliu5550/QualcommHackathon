# LLM Models Directory

This directory contains exported ONNX models for lightweight runtime inference.

## Directory Structure

Each exported model has its own subdirectory:

```
models/
├── Llama-3.2-3B-Instruct/     # Default model
│   ├── decoder_model.onnx      # Main ONNX model (FP16)
│   ├── tokenizer.json          # Tokenizer
│   ├── config.json             # Model config
│   └── generation_config.json  # Generation settings
├── Other-Model-Name/           # Other models (if exported)
│   └── ...
├── README.md                   # This file
└── .gitignore
```

## Overview

The ONNX models provide **5-10x faster startup** and **~80% smaller installation size** compared to PyTorch-based inference, while preserving original FP16 precision.

### Architecture

1. **Export Stage** (Development Only)
   - Requires: `torch`, `transformers`, `optimum`
   - Run once: `fileorg-export-llm`
   - Creates: `models/{model_name}/` directory with ONNX files

2. **Runtime Stage** (Production)
   - Requires: `onnxruntime-gpu`, `tokenizers` (lightweight)
   - Uses: `OnnxProvider(model_name="Llama-3.2-3B-Instruct")`
   - Supports: CUDA, CoreML, QNN, CPU

## Quick Start

### Step 1: Export Model (One-time Setup)

**For Developers:**

```bash
# Install export dependencies
uv pip install -e '.[llm-export]'

# Export default model (Llama 3.2 3B Instruct)
fileorg-export-llm --yes

# Export different model
fileorg-export-llm --model meta-llama/Llama-3.2-8B-Instruct --yes
```

**Expected Output:**
```
fileorg/llm_classifier/models/
└── Llama-3.2-3B-Instruct/
    ├── decoder_model.onnx        (~6 GB, FP16)
    ├── tokenizer.json            (~1.8 MB)
    ├── config.json
    └── generation_config.json
```


## Supported Hardware

| Platform | Execution Provider | Performance |
|----------|-------------------|-------------|
| **NVIDIA GPU** | CUDAExecutionProvider | TO_TEST |
| **Apple Silicon** | CoreMLExecutionProvider | TO_TEST |
| **Qualcomm NPU** | QNNExecutionProvider | TO_TEST |
| **CPU** | CPUExecutionProvider | TO_TEST |

## Model Details

### Default Model: Llama 3.2 3B Instruct

- **Source**: `meta-llama/Llama-3.2-3B-Instruct`
- **Precision**: FP16 (preserved from original model weights)
- **File Size**: ~6 GB (ONNX model directory)
- **Context Length**: Up to 128K tokens (hardware limited)
- **License**: Llama 3.2 Community License
- **Export Task**: `text-generation-with-past` (with KV cache support)

## Usage

### Export

```bash
# Install export dependencies (simplified, no quantization tools included)
uv pip install -e '.[llm-export]'

# Export the default model
fileorg-export-llm --yes

# Export a different model
fileorg-export-llm --model meta-llama/Llama-3.2-8B-Instruct --yes
```

### Runtime

```bash
# Install runtime dependencies (onnxruntime-gpu, tokenizers)
uv pip install -e .

# Use the ONNX provider
from fileorg.llm_classifier.adapters.llm_providers.onnx_provider import OnnxProvider

# Default model
provider = OnnxProvider()  # Automatically loads Llama-3.2-3B-Instruct

# Or specify a model explicitly
provider = OnnxProvider(model_name="Llama-3.2-3B-Instruct")
```


## Comparison: ONNX vs PyTorch

| Metric | ONNX Runtime | PyTorch |
|--------|--------------|---------|
| **Installation Size** | ~2 GB | ~10 GB |
| **Startup Time** | ~2-3 seconds | ~15-30 seconds |
| **Memory Usage** | ~7 GB | ~8-9 GB |
| **Inference Speed** | Baseline | ~5-10% slower |
| **Dependencies** | `onnxruntime-gpu`, `tokenizers` | `torch`, `transformers` |
| **Production Ready** | ✅ Yes | ⚠️ Heavy |


## License & Attribution

The exported models inherit the license from the source model:
- Llama 3.2 models: [Llama 3.2 Community License](https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/LICENSE)

This export tool uses:
- ONNX Runtime: MIT License
- Optimum: Apache 2.0 License