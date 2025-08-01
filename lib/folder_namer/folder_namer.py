from typing import List, Dict, Any
import json
import re

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
        create_folder = self.llm.inference(prompt = messages,max_new_tokens= 200) ## 這部分可能會有問題，plpeline有點限制太多，我想用generate方式使用
        return self.clean_output(create_folder)

    def remapping_folder(self, candidate_folder:List[str]):
        """
        INPUT: ["account", ""]
        create_folder_name會每一個檔案都建立一個檔案夾名稱，此函數用意是將相同的意義的檔案夾名稱聚合在一起
        產出是，前面是foldername原先的資料夾名稱，groupname應該要合併到這個資料夾名稱
        [
            {"foldername": "/Famine in Gaza", "groupname": "Famine"},
            {"foldername": "/Screen Time: The Dark Side", "groupname": "Screen Time"},
            ...
            {"foldername": "/Screen Move: The Dark Side", "groupname": "Screen Time"},
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
        
        # 推論 (你可以自行切換 generate / pipeline)
        mapp_folder = self.llm.inference(prompt=messages, max_new_tokens=400)

        try:
            # 嘗試解析 JSON，如果失敗則手動修復
            if not mapp_folder.startswith('['):
                mapp_folder = '[{"foldername":"' + mapp_folder
            if not mapp_folder.endswith(']'):
                mapp_folder = mapp_folder.rstrip(',') + ']'
            
            data = json.loads(mapp_folder)
        except json.JSONDecodeError as e:
            print(f"JSON decode failed: {e}\nOutput: {mapp_folder}")
            # 如果 JSON 解析失敗，返回原始映射
            data = [{"foldername": folder, "groupname": folder} for folder in candidate_folder]

        # 清理資料夾名稱與群組名稱
        for item in data:
            item["foldername"] = item["foldername"].lstrip('/')
            item["groupname"] = self.clean_output(item["groupname"])

        return data
    

    def clean_output(self, text: str) -> str:
        # 保留中文、英文大小寫與阿拉伯數字，其餘全部移除
        cleaned = re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9\s]', '', text)
        return cleaned.strip()

    def process_files(self, summaries_data: Dict[str, Any], base_output_dir: str = "./") -> Dict[str, List[Dict[str, str]]]:
        """
        主要處理函數，整合所有步驟
        
        Args:
            summaries_data: 包含 summaries 列表的字典，每個元素包含 summary, path, name
            base_output_dir: 輸出目錄的基礎路徑(使用者輸入的路徑)
            
        Returns:
            包含 file_paths 列表的字典
            {
            "file_paths": [
                {
                    "initial_path": "./documents/init_folder/CH04account.pdf",
                    "original": "./documents/Accounting/CH04account.pdf", 
                    "new": "./documents/AcademicSubjects/CH04account.pdf"
                },
                {
                    "initial_path": "./documents/init_folder/Ch4  Principles component analysis(2)(1).pdf",
                    "original": "./documents/Statistics/Ch4  Principles component analysis(2)(1).pdf",
                    "new": "./documents/AcademicSubjects/Ch4  Principles component analysis(2)(1).pdf"
                }
            ]
        }
        """
        summaries = summaries_data.get("summaries", [])
        
        # 步驟 1: 為每個檔案創建資料夾名稱
        print("步驟 1: 為每個檔案創建資料夾名稱...")
        file_folder_mapping = []
        candidate_folders = []
        
        for summary_item in summaries:
            content = summary_item["summary"][:500]  # 限制內容長度避免 token 過多
            folder_name = self.create_folder_name(content)
            
            file_folder_mapping.append({
                "original_path": summary_item["path"],
                "name": summary_item["name"],
                "initial_folder": folder_name
            })
            candidate_folders.append(folder_name)
        
        print(f"初始資料夾名稱: {candidate_folders}")
        
        # 步驟 2: 合併相似的資料夾名稱
        print("步驟 2: 合併相似的資料夾名稱...")
        if len(candidate_folders) > 1:
            folder_mappings = self.remapping_folder(candidate_folders)
        else:
            # 如果只有一個檔案，不需要合併
            folder_mappings = [{"foldername": candidate_folders[0], "groupname": candidate_folders[0]}] if candidate_folders else []
        
        # 創建 folder_name -> group_name 的映射
        folder_to_group = {}
        for mapping in folder_mappings:
            folder_to_group[mapping["foldername"]] = mapping["groupname"]
        
        # 步驟 3: 生成最終的檔案路徑映射
        file_paths = []
        
        for file_info in file_folder_mapping:
            file_name = file_info["name"]
            initial_folder = file_info["initial_folder"]
            
            # 查找對應的群組名稱
            group_name = folder_to_group.get(initial_folder, initial_folder)
            
            # 構建路徑
            initial_path = f"{base_output_dir}/init_folder/{file_name}"
            old_path = f"{base_output_dir}/{initial_folder}/{file_name}"
            new_path = f"{base_output_dir}/{group_name}/{file_name}"
            
            file_paths.append({
                "initial_path": initial_path,
                "original": old_path,
                "new": new_path
            })
        
        result = {"file_paths": file_paths}

        return result

    def save_result(self, result: Dict[str, Any], output_file: str = "file_mapping_result.json"):
        """
        儲存結果到 JSON 檔案
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"結果已儲存到: {output_file}")

    
create_name = CreateFolderNamer()
