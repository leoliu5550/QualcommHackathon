from lib.llm_model.llm_interface import get_llm
from lib.llm_model.mode_config import config


class CreateFolderNamer:
    def __init__(self) -> None:
        self.llm = get_llm(
            backend=config.get("backend"),
            model_id=config.get("model_id"),
            # dlc_path=config.get("dlc_path"),
            # tokenizer_id=config.get("tokenizer_id"),
        )
        pass

    def create_folder_name(self, content: str):
        """
        輸入部分的檔案文字後產出合適的folder_name
        一份檔案就會有一個folder_name
        """
        pmt = "give me an appropriate folder name of the content must in json format:"
        txt = content
        cnt = pmt + txt
        messages = [
            {
                "role": "system",
                "content": 'you are a master of categorizing content and give it a folder name in json format, eg. {"foldername": "/foldername"}',
            },
            {"role": "user", "content": cnt},
            {"role": "assistant", "content": '{"foldername": "'},
        ]
        create_folder = self.llm.inference(messages,max_new_tokens= 20) ## 這部分可能會有問題，plpeline有點限制太多，我想用generate方式使用
        return create_folder


