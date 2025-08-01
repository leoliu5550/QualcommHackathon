from lib.llm_model.llm_interface import get_llm
from lib.llm_model.mode_config import config
from lib.service.organize_service import Organizer

def main():
    llm = get_llm(
        backend=config.get("backend"),
        model_id=config.get("model_id"),
        # dlc_path=config.get("dlc_path"),
        # tokenizer_id=config.get("tokenizer_id"),
    )

    # 標準接口（比賽或串接都統一呼叫）
    prompt = [
    {
        "role": "user",
        "content": (
            "You are a JSON API. Respond only in JSON. Do not say anything else. Do not explain. "
            "Format strictly like this:\n\n"
            '{\n  "answer": "..." \n}\n\n'
            "Now respond to the question using this format.\n"
            "Question: What is the capital of France?"
        )
    }
]
    for _ in range(4):
        result = llm.inference(prompt,max_new_tokens= 100)
        print(result)
        print("="*10)

    # organizer = Organizer()
    # organizer.start_organize(target_path="test/data/filetype")


if __name__=="__main__":
    main()