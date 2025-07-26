from typing import List

class BaseLLM:
    def inference(self, prompt: str) -> str:
        raise NotImplementedError("Must implement in subclass")

# 本地 RTX/transformers 實作
class LocalTransformersLLM(BaseLLM):
    def __init__(self, model_id: str, device: str = "cuda"):
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id).to(device)
        self.llm = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer, device=0 if device == "cuda" else -1)

    def inference(self, prompt: str, max_new_tokens: int = 128) -> str:
        output = self.llm(prompt, max_new_tokens=max_new_tokens, do_sample=True, temperature=0.7)[0]["generated_text"]
        return output

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

