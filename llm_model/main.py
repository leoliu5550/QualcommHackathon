from llm_interface import get_llm

# 設定（方便 config/環境切換）
config = {
    "backend": "local",  # "local" 或 "qualcomm"
    "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    # "dlc_path": "tinyllama.dlc",   # 若用 qualcomm
    # "tokenizer_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
}

if __name__ == "__main__":
    llm = get_llm(
        backend=config["backend"],
        model_id=config.get("model_id"),
        # dlc_path=config.get("dlc_path"),
        # tokenizer_id=config.get("tokenizer_id"),
    )

    # 標準接口（比賽或串接都統一呼叫）
    prompt = "我們的資料結構及每個檔案的部分資訊如下:"
    result = llm.inference(prompt)
    print(f"Prompt: {prompt}\n===\n{result}\n{'='*30}")
