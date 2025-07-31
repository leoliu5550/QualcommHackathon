from typing import List
import json
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
        一份檔案就會有一個folder_name，實際上LLM 的產出會是一個字串像是"Christmas in August"
        輸入部分的檔案文字後產出合適的folder_name，格式: /foldername
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
        create_folder = self.llm.inference(prompt = messages,max_new_tokens= 20) ## 這部分可能會有問題，plpeline有點限制太多，我想用generate方式使用
        return create_folder

    def remapping_folder(self, candidate_folder:List[str]):
        """
        create_folder_name會每一個檔案都建立一個檔案夾名稱，此函數用意是將相同的意義的檔案夾名稱聚合在一起
        產出是，前面是foldername原先的資料夾名稱，groupname應該要合併到這個資料夾名稱
        [
            {"foldername": "/Famine in Gaza", "groupname": "Famine"},
            {"foldername": "/Screen Time: The Dark Side", "groupname": "Screen Time"},
        ]
        """
        pmt = "categorize the foldername into several groups if they are related or similar and give each group a name, must in json format:"
        txt = "[" + ", ".join(candidate_folder) + "]"
        cnt = pmt+txt
        messages = [
            {"role": "system", "content": 'you are a master of categorizing folder names and give it a new group name in json format, eg. {"foldername":"/foldername", "groupname":"/groupname"]}'},
            {"role": "user", "content": cnt},
            {"role": "assistant", "content": '{"groups": ["'},
        ]
        mapp_folder = self.llm.inference(prompt = messages,max_new_tokens= 400) ## 這部分可能會有問題，plpeline有點限制太多，我想用generate方式使用
        """
        [
            {"foldername": "/Famine in Gaza", "groupname": "Famine"},
            {"foldername": "/Screen Time: The Dark Side", "groupname": "Screen Time"},
        ]
        """
        # 1. 字串轉 Python 物件
        data = json.loads(mapp_folder)

        # 2. 去掉每個 foldername 的開頭斜線
        for item in data:
            item["foldername"] = item["foldername"].lstrip('/')

        return data
