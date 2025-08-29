"""FileOrg AI Interface Module

Unified interface for various AI backends including local GPU/CPU and NPU implementations.
"""

from typing import List
import httpx
from fileorg.ai.config import config


class BaseLLM:
    """Abstract base class for all LLM implementations."""
    
    def inference(self, prompt: str) -> str:
        """Perform inference on the given prompt.
        
        Args:
            prompt: Input text for the model
            
        Returns:
            Generated response from the model
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Must implement in subclass")


class LocalTransformersLLM(BaseLLM):
    """Local transformer-based LLM implementation for GPU/CPU inference.
    
    Uses Hugging Face transformers library with automatic hardware detection.
    Supports both CUDA and CPU execution with graceful fallback.
    """
    
    def __init__(self, model_id: str, device: str = "cuda"):
        """Initialize local transformer model.
        
        Args:
            model_id: Hugging Face model identifier
            device: Computing device ('cuda' or 'cpu')
        """
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        except ImportError as e:
            raise ImportError(
                "Local backend requires transformers and torch. "
                "Install with: pip install fileorg[non-npu]"
            ) from e
        
        model_dir = "./fileorg/ai/model"
        
        # Auto-detect device availability
        if device == "cuda" and not torch.cuda.is_available():
            self.device = "cpu"
        else:
            self.device = device
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=model_dir)
        
        # Load model with automatic quantization fallback
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                cache_dir=model_dir
            ).to(self.device)
        except (ImportError, Exception) as e:
            error_str = str(e)
            # Handle missing quantization dependencies
            if any(x in error_str for x in ["bitsandbytes", "quantization", "No package metadata"]):
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    cache_dir=model_dir,
                    quantization_config=None,
                    load_in_4bit=False,
                    load_in_8bit=False
                ).to(self.device)
            else:
                raise
        
        # Create text generation pipeline
        self.llm = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            return_full_text=False
        )
    
    def inference(self, prompt: str, max_new_tokens: int = 128) -> str:
        """Generate text using the local model.
        
        Args:
            prompt: Input text to process
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        output = self.llm(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.1
        )[0]["generated_text"]
        return output


class QualcommLLM(BaseLLM):
    """Qualcomm Snapdragon NPU optimized LLM implementation.
    
    Currently uses NPU API endpoint for inference.
    Future versions will support direct SNPE/QNN integration.
    """
    
    def __init__(self, **kwargs):
        """Initialize Qualcomm NPU backend.
        
        Args:
            **kwargs: Reserved for future SNPE/QNN configuration
        """
        pass  # Current implementation uses API, no initialization needed
    
    def inference(self, prompt: str, max_new_tokens: int = 64) -> str:
        """Perform NPU-accelerated inference via API.
        
        Args:
            prompt: Input text for processing  
            max_new_tokens: Maximum tokens to generate (unused in API mode)
            
        Returns:
            Generated response from NPU
        """
        return self._call_npu_api(prompt)
    
    def _call_npu_api(self, prompt: str) -> str:
        """Call Qualcomm NPU API endpoint.
        
        Args:
            prompt: Input messages for the model
            
        Returns:
            Generated text response
        """
        # API configuration
        api_key = "3dc12b8ca6fcdccf75a6010e95eca4ca7c8827604c10381686912eb746d41f60"
        url = "http://127.0.0.1:80/v1.0/chat/completions"
        model_name = ".bot/Llama 3.1 8B @NPU"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model_name,
            "messages": prompt,
            "temperature": 0.1
        }
        
        with httpx.Client(timeout=600.0) as client:
            response = client.post(url, headers=headers, json=payload)
        
        return response.json()["choices"][-1]["message"]["content"]
            





def get_llm(backend: str, **kwargs) -> BaseLLM:
    """Factory function to create appropriate LLM backend.
    
    Args:
        backend: Backend type ('local' or 'qualcomm')
        **kwargs: Backend-specific initialization parameters
        
    Returns:
        Configured LLM instance
        
    Raises:
        ValueError: If backend is not recognized
    """
    if backend == "local":
        return LocalTransformersLLM(**kwargs)
    elif backend == "qualcomm":
        return QualcommLLM(**kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")


if __name__ == "__main__":
    # Example usage
    llm = get_llm(
        backend=config.get("backend"),
        model_id=config.get("model_id"),
    )
    
    prompt = "Categorize this document:"
    result = llm.inference(prompt)
    print(f"Prompt: {prompt}\nResult: {result}")
