from typing import List

import torch

from lib.llm_model.mode_config import config

class BaseLLM:
    def inference(self, prompt: str) -> str:
        raise NotImplementedError("Must implement in subclass")

# 本地 RTX/transformers 實作
class LocalTransformersLLM(BaseLLM):
    def __init__(self, model_id: str, device: str = "cuda"):
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        model_dir = "./lib/llm_model/model"

        # 檢查 CUDA 可用性，若不可用則切換到 CPU
        if device == "cuda" and not torch.cuda.is_available():
            # print("[LocalTransformersLLM] CUDA not available, switching to CPU")
            self.device = "cpu"
        else:
            self.device = device  # "cuda" or "cpu"

        # pipeline 需要的 device_idx，CPU 用 -1，CUDA 用 0
        # device_idx = 0 if self.device == "cuda" else -1
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=model_dir)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, cache_dir=model_dir).to(self.device)
    #     self.llm = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer, device=device_idx,
    # return_full_text=False)

    # def inference(self, prompt: str, max_new_tokens: int = 128) -> str:
    #     output = self.llm(prompt, max_new_tokens=max_new_tokens, do_sample=False, temperature=0)[0]["generated_text"]
    #     return output
    def inference(self, messages: list[dict], max_new_tokens: int = 128) -> str:
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(self.model.device)

        output_ids = self.model.generate(inputs, max_new_tokens=max_new_tokens)
        output_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return output_text
# 假設 SNPE Python API 已安裝（決賽時補上 import snpe 等…）
# from snpe import ... (依實際情境引入)
class QualcommLLM(BaseLLM):
    """
    Qualcomm/SNPE LLM 推理接口，input/output = str。
    適用於 Snapdragon X/Windows（決賽時將推理部分補齊）。
    """
    def __init__(self, dlc_path: str, tokenizer_id: str):
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
        統一 LLM 推理函數，input/output 皆為 str。
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

# LLM 工廠：決定用哪個 backend
def get_llm(backend: str, **kwargs) -> BaseLLM:
    if backend == "local":
        return LocalTransformersLLM(**kwargs)
    elif backend == "qualcomm":
        return QualcommLLM(**kwargs)
    else:
        raise ValueError(f"Unknown backend: {backend}")

if __name__ == "__main__":
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
