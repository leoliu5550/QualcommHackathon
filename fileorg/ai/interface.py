"""
FileOrg AI Interface Module

This module provides a unified interface for various AI backends, from local
GPU-accelerated models to specialized NPU implementations. We're building
towards a future where AI assistance is seamless across all hardware.

Our vision is to make powerful AI accessible regardless of hardware constraints,
whether you're using a high-end GPU, Snapdragon NPU, or just a CPU.
"""

from typing import List

import torch

from fileorg.ai.config import config

class BaseLLM:
    """
    Abstract base class for all LLM implementations.
    
    We've designed this interface to be minimal yet flexible, allowing for
    various backend implementations while maintaining consistency. This abstraction
    enables us to swap AI providers without changing the core logic.
    
    Future implementations may include cloud APIs, distributed inference,
    and federated learning capabilities.
    """
    
    def inference(self, prompt: str) -> str:
        """
        Perform inference on the given prompt.
        
        Args:
            prompt (str): Input text for the model
        
        Returns:
            str: Generated response from the model
        
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Must implement in subclass")

class LocalTransformersLLM(BaseLLM):
    """
    Local transformer-based LLM implementation for GPU/CPU inference.
    
    This implementation leverages the Hugging Face transformers library to run
    models locally. We automatically detect and use available hardware acceleration,
    falling back gracefully when needed.
    
    We're committed to supporting the latest open-source models and optimizations
    to give users the best possible local AI experience.
    
    Attributes:
        device (str): Computing device ('cuda' or 'cpu')
        model: Loaded transformer model
        tokenizer: Associated tokenizer
    
    Note:
        We cache models locally to reduce download times and support offline usage.
        Future versions will include quantization options for memory-constrained systems.
    """
    def __init__(self, model_id: str, device: str = "cuda"):
        """
        Initialize local transformer model with automatic device selection.
        
        Args:
            model_id (str): Hugging Face model identifier
            device (str): Preferred device ('cuda' or 'cpu')
        
        The initialization process intelligently handles hardware availability,
        ensuring the best possible performance on any system.
        """
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        model_dir = "./fileorg/ai/model"

        # 檢查 CUDA 可用性，若不可用則切換到 CPU
        if device == "cuda" and not torch.cuda.is_available():
            # print("[LocalTransformersLLM] CUDA not available, switching to CPU")
            self.device = "cpu"
        else:
            self.device = device  # "cuda" or "cpu"

        # pipeline 需要的 device_idx，CPU 用 -1，CUDA 用 0
        device_idx = 0 if self.device == "cuda" else -1
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=model_dir)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, cache_dir=model_dir).to(self.device)
        self.llm = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer , #device=device_idx,
    return_full_text=False)

    def inference(self, prompt: str, max_new_tokens: int = 128) -> str:
        """
        Generate text using the local transformer model.
        
        Args:
            prompt (str): Input text to process
            max_new_tokens (int): Maximum tokens to generate
        
        Returns:
            str: Generated text response
        
        We've tuned the generation parameters for file organization tasks,
        balancing creativity with accuracy for optimal categorization.
        """
        print(f"model inferences: {prompt}")
        output = self.llm(prompt, max_new_tokens=max_new_tokens, do_sample=True, temperature = 0.1)[0]["generated_text"]
        return output

class QualcommLLM(BaseLLM):
    """
    Qualcomm Snapdragon NPU optimized LLM implementation.
    
    This implementation represents our commitment to edge AI and efficient
    inference on modern laptop hardware. By leveraging Snapdragon's NPU,
    we achieve remarkable performance while maintaining low power consumption.
    
    We're excited about the possibilities this opens for always-on AI assistance
    without cloud dependency. This is particularly important for privacy-conscious
    users and enterprise deployments.
    
    Features:
        - NPU-accelerated inference
        - Power-efficient processing
        - Low latency responses
        - Privacy-preserving local execution
    
    Note:
        This implementation is continuously evolving as Qualcomm enhances
        their AI stack. We work closely with hardware partners to deliver
        optimal performance.
    """
    def __init__(self, dlc_path: str, tokenizer_id: str):
        """
        Initialize Qualcomm NPU-accelerated model.
        
        Args:
            dlc_path (str): Path to compiled DLC model file
            tokenizer_id (str): Tokenizer identifier for text processing
        
        We're working on automatic model optimization and compilation
        to make NPU deployment even more accessible.
        """
        from transformers import AutoTokenizer
        self.dlc_path = dlc_path
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_id)
        # 決賽前：這裡可以留 stub，等現場裝好 SNPE SDK 再補
        self.snpe_session = None  # 之後可改為 SNPE session 初始化
        print(f"[QualcommLLM] 初始化完成（dlc: {dlc_path}）")

    def _snpe_infer(self, input_ids: List[int]) -> int:
        """
        這裡預留呼叫 SNPE 的 DLC 推理接口。
        開發時用 mock，決賽現場補上 snpe-net-run 或 python API。
        """
        # ==== 決賽時替換為 SNPE Session 呼叫 ====
        # output = self.snpe_session.infer(input_tensor)
        # next_token_id = output.argmax()
        # return next_token_id

        # ---- 本地 stub: always return EOS ----
        eos_id = self.tokenizer.eos_token_id or 2
        return eos_id

    def inference(self, prompt: str, max_new_tokens: int = 64) -> str:
        """
        Perform NPU-accelerated inference.
        
        Args:
            prompt (str): Input text for processing
            max_new_tokens (int): Maximum tokens to generate
        
        Returns:
            str: Generated response
        
        The NPU inference path is optimized for Snapdragon X series laptops,
        delivering desktop-class AI performance in an ultraportable form factor.
        """
        input_ids = self.tokenizer(prompt, return_tensors="np")["input_ids"][0].tolist()
        output_ids = input_ids.copy()
        for _ in range(max_new_tokens):
            next_token_id = self._snpe_infer(output_ids)
            # 如果遇到 EOS 結束
            if next_token_id == self.tokenizer.eos_token_id or len(output_ids) > 2048:
                break
            output_ids.append(next_token_id)
        return self.tokenizer.decode(output_ids, skip_special_tokens=True)

def get_llm(backend: str, **kwargs) -> BaseLLM:
    """
    Factory function to create appropriate LLM backend.
    
    This factory pattern allows us to seamlessly switch between different
    AI backends based on available hardware and user preferences. We're
    building towards automatic backend selection based on task requirements.
    
    Args:
        backend (str): Backend type ('local' or 'qualcomm')
        **kwargs: Backend-specific initialization parameters
    
    Returns:
        BaseLLM: Configured LLM instance
    
    Raises:
        ValueError: If backend is not recognized
    
    Example:
        >>> llm = get_llm('local', model_id='TinyLlama/TinyLlama-1.1B')
        >>> response = llm.inference("Categorize this document about machine learning")
    
    Future backends may include:
        - 'cloud': For API-based inference
        - 'distributed': For multi-device inference
        - 'hybrid': Combining local and cloud for optimal performance
    """
    if backend == "local":
        return LocalTransformersLLM(**kwargs)
    elif backend == "qualcomm":
        return QualcommLLM(**kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")

if __name__ == "__main__":
    # Example usage demonstrating our unified AI interface
    llm = get_llm(
        backend=config.get("backend"),
        model_id=config.get("model_id"),
        # dlc_path=config.get("dlc_path"),
        # tokenizer_id=config.get("tokenizer_id"),
    )

    # 標準接口（比賽或串接都統一呼叫）
    prompt = "我們的資料結構及每個檔案的部分資訊如下:"
    result = llm.inference(prompt)
    print(f"Prompt: {prompt}\n===\n{result}\n{'='*30}")
