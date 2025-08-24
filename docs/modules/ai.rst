AI Interface
============

This module provides a unified interface for various AI backends, from local GPU-accelerated
models to specialized NPU implementations. We're building towards a future where AI assistance
is seamless across all hardware.

.. automodule:: fileorg.ai.interface
   :members:
   :undoc-members:
   :show-inheritance:

Supported Backends
------------------

Local Transformers
~~~~~~~~~~~~~~~~~

For users with GPUs or powerful CPUs:

- Automatic hardware detection
- Hugging Face model integration
- Offline operation
- Privacy-preserving local inference

Qualcomm NPU
~~~~~~~~~~~~

Optimized for Snapdragon X series laptops:

- NPU-accelerated inference
- Power-efficient processing  
- Low latency responses
- Enterprise-grade privacy

Configuration
-------------

Backend selection is handled automatically based on available hardware:

.. code-block:: python

   from fileorg.ai.interface import get_llm
   
   # Automatic backend selection
   llm = get_llm('local', model_id='TinyLlama/TinyLlama-1.1B')
   
   # NPU acceleration (when available)
   llm = get_llm('qualcomm', dlc_path='model.dlc', tokenizer_id='tokenizer')

Future Backends
---------------

We're exploring:

- Cloud API integration
- Distributed inference across devices
- Hybrid local-cloud processing
- Federated learning capabilities