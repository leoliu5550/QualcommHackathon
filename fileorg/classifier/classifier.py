"""Document classification and folder naming module.

Provides intelligent document categorization using LLM backends.
Supports multiple prompt versions for backward compatibility.
"""

from typing import List, Dict, Any
import json
import re
import os

from fileorg.ai.interface import get_llm
from fileorg.ai.config import config
from .prompt_versions import (
    get_prompt_version,
    get_version_features,
    detect_domain,
    migrate_config
)


class CreateFolderNamer:
    """Document classifier for intelligent folder naming.
    
    Attributes:
        llm: Language model interface for inference.
        prompt_version: Prompt template version ('v1' or 'v2').
        use_few_shot: Include few-shot examples in prompts.
        use_domain_detection: Auto-detect content domain.
    """
    
    def __init__(self, use_advanced_prompt: bool = False, prompt_version: str = "v1",
                 use_few_shot: bool = False, use_domain_detection: bool = False):
        """Initialize folder naming tool.
        
        Args:
            use_advanced_prompt: Enable advanced features (default: False).
            prompt_version: Template version 'v1' or 'v2' (default: 'v1').
            use_few_shot: Include few-shot examples (default: False).
            use_domain_detection: Auto-detect domain (default: False).
        """
        self.llm = get_llm(
            backend=config.get("backend"),
            model_id=config.get("model_id"),
        )
        
        # Determine prompt version based on configuration
        if use_advanced_prompt:
            self.prompt_version = prompt_version
        else:
            # For backward compatibility
            self.prompt_version = "v1"
        
        # Load prompt configuration
        try:
            self.prompt_config = get_prompt_version(self.prompt_version)
            self.features = get_version_features(self.prompt_version)
        except ValueError:
            # Fallback to v1 if version not found
            self.prompt_version = "v1"
            self.prompt_config = get_prompt_version("v1")
            self.features = get_version_features("v1")
        
        # Apply feature flags (respecting version capabilities)
        self.use_few_shot = use_few_shot and self.features.get("few_shot", False)
        self.use_domain_detection = use_domain_detection and self.features.get("domain_detection", False)
    
    def create_folder_name(self, content: str) -> str:
        """Generate folder name for file content.
        
        Args:
            content: File content to classify (max 500 chars used).
        
        Returns:
            Cleaned folder name with alphanumeric and Chinese characters.
        """
        # Truncate content if needed
        if len(content) > 500:
            content = content[:500]
        
        # Build prompt messages using centralized prompt version
        messages = self._build_classification_prompt(content)
        
        # Call LLM
        create_folder = self.llm.inference(prompt=messages, max_new_tokens=200)
        
        # Clean and return output
        return self.clean_output(create_folder)
    
    def _build_classification_prompt(self, content: str) -> List[Dict[str, str]]:
        """Build classification prompt.
        
        Args:
            content: Content to classify.
            
        Returns:
            List of message dictionaries for LLM.
        """
        messages = []
        
        # Add system message
        messages.append({
            "role": "system",
            "content": self.prompt_config["system"]
        })
        
        # Add few-shot examples if enabled and available
        if self.use_few_shot and "examples" in self.prompt_config:
            for example in self.prompt_config["examples"][:2]:  # Use first 2 examples
                messages.append({
                    "role": "user",
                    "content": self.prompt_config["prompt_prefix"] + example["input"]
                })
                messages.append({
                    "role": "assistant",
                    "content": example["output"]
                })
        
        # Add actual content to classify
        user_content = self.prompt_config["prompt_prefix"] + content
        messages.append({"role": "user", "content": user_content})
        
        # Add assistant prefix to guide output format
        messages.append({
            "role": "assistant",
            "content": self.prompt_config["assistant_prefix"]
        })
        
        return messages
    
    def remapping_folder(self, candidate_folder: List[str]) -> List[Dict[str, str]]:
        """Group similar folder names.
        
        Args:
            candidate_folder: List of folder names to group.
        
        Returns:
            List of dicts mapping original names to group names.
        """
        # Build remapping prompt
        messages = self._build_remapping_prompt(candidate_folder)
        
        # Call LLM
        mapp_folder = self.llm.inference(prompt=messages, max_new_tokens=400)
        
        # Parse and validate output
        try:
            # Try to fix common JSON issues
            if not mapp_folder.startswith('['):
                mapp_folder = '[{"foldername":"' + mapp_folder
            if not mapp_folder.endswith(']'):
                mapp_folder = mapp_folder.rstrip(',') + ']'
            
            data = json.loads(mapp_folder)
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}\nOutput: {mapp_folder}")
            # Fallback to identity mapping
            data = [{"foldername": folder, "groupname": folder} for folder in candidate_folder]
        
        # Clean folder names
        for item in data:
            item["foldername"] = item["foldername"].lstrip('/')
            item["groupname"] = self.clean_output(item["groupname"])
        
        return data
    
    def _build_remapping_prompt(self, candidate_folder: List[str]) -> List[Dict[str, str]]:
        """Build remapping prompt.
        
        Args:
            candidate_folder: Folder names to group.
            
        Returns:
            List of message dictionaries for LLM.
        """
        # Check if version supports remapping
        if not self.features.get("remapping", False):
            # Fallback to simple prompt for v1
            pmt = "categorize the foldername into several groups if they are related or similar and give each group a name, must in json format:"
            txt = "[" + ", ".join(candidate_folder) + "]"
            cnt = pmt + txt
            messages = [
                {"role": "system", "content": 'you are a master of categorizing folder names and give it a new group name in json format, eg. {"foldername":"/foldername", "groupname":"/groupname"]}'},
                {"role": "user", "content": cnt},
                {"role": "assistant", "content": '{"groups": ["'},
            ]
            return messages
        
        # Use v2 remapping system if available
        messages = []
        
        # Add remapping system message
        messages.append({
            "role": "system",
            "content": self.prompt_config.get("remapping_system", self.prompt_config["system"])
        })
        
        # Add user content
        folder_list = "[" + ", ".join(f'"{f}"' for f in candidate_folder) + "]"
        user_content = self.prompt_config.get("remapping_prefix", "Group these folders: ") + folder_list
        messages.append({"role": "user", "content": user_content})
        
        # Add assistant prefix
        messages.append({
            "role": "assistant",
            "content": self.prompt_config.get("remapping_assistant_prefix", '[{"foldername":"')
        })
        
        return messages
    
    def clean_output(self, text: str) -> str:
        """Clean LLM output for folder names.
        
        Args:
            text: Raw LLM output.
            
        Returns:
            Cleaned text with only alphanumeric, Chinese, and spaces.
        """
        # 保留中文、英文大小寫與阿拉伯數字、空格，其餘全部移除（包括斜線）
        cleaned = re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9\s]', '', text)
        
        # 移除 "foldername" 這個字眼，不分大小寫
        cleaned = re.sub(r'foldername', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()

        return cleaned.strip()
    
    def process_files(self, summaries_data: Dict[str, Any], base_output_dir: str = "./") -> Dict[str, List[Dict[str, str]]]:
        """Process files and organize into folders.
        
        Args:
            summaries_data: Dict with 'summaries' list containing summary, path, name.
            base_output_dir: Base output directory (default: './').
        
        Returns:
            Dict with 'file_paths' list of original/new path mappings.
        """
        summaries = summaries_data.get("summaries", [])
        
        # 第一步：幫每個檔案取個資料夾名稱
        print("第一步：幫每個檔案取個資料夾名稱...")
        file_folder_mapping = []
        candidate_folders = []
        
        for summary_item in summaries:
            content = summary_item["summary"][:500]  # 只取前500個字，避免內容太長
            folder_name = self.create_folder_name(content)
            
            file_folder_mapping.append({
                "original_path": summary_item["path"],
                "name": summary_item["name"],
                "initial_folder": folder_name
            })
            candidate_folders.append(folder_name)
        
        print(f"初始資料夾名稱: {candidate_folders}")
        
        # 第二步：把相似的資料夾名稱合併在一起
        print("第二步：把相似的資料夾名稱合併在一起...")
        if len(candidate_folders) > 1:
            folder_mappings = self.remapping_folder(candidate_folders)
        else:
            # 只有一個檔案的話，就不用合併了
            folder_mappings = [{"foldername": candidate_folders[0], "groupname": candidate_folders[0]}] if candidate_folders else []
        
        # 建立資料夾名稱對應到群組名稱的對照表
        folder_to_group = {}
        for mapping in folder_mappings:
            folder_to_group[mapping["foldername"]] = mapping["groupname"]
        
        # 第三步：產生最終的檔案路徑對應表
        file_paths = []
        
        for file_info in file_folder_mapping:
            file_name = file_info["name"]
            initial_folder = file_info["initial_folder"]
            
            # 找出對應的群組名稱
            group_name = folder_to_group.get(initial_folder, initial_folder)
            
            # 建立路徑
            old_path = file_info["original_path"]
            new_path = os.path.join(base_output_dir, group_name, file_name)
            
            file_paths.append({
                "original": old_path,
                "new": new_path
            })
        
        result = {"file_paths": file_paths}
        
        return result
    
    def save_result(self, result: Dict[str, Any], output_file: str = "file_mapping_result.json"):
        """Save results to JSON.
        
        Args:
            result: File mapping results.
            output_file: Output path (default: 'file_mapping_result.json').
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"結果已儲存到: {output_file}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics.
        
        Returns:
            Optimization stats dict or empty dict if disabled.
        """
        if self.use_advanced_prompt and self.prompt_optimizer:
            return self.prompt_optimizer.get_optimization_stats()
        return {}


# Singleton pattern for model state management
_create_name_instance = None


def get_create_name():
    """Get singleton CreateFolderNamer instance.
    
    Returns:
        CreateFolderNamer: Singleton instance
    """
    global _create_name_instance
    if _create_name_instance is None:
        from fileorg.ai.config import Config
        cfg = Config()
        
        # Get version from config (using new centralized version management)
        version = cfg.get("prompt_version", cfg.get("classifier_version", "v2"))
        
        # Determine if we should use advanced features based on version
        use_advanced = version != "v1"
        
        _create_name_instance = CreateFolderNamer(
            use_advanced_prompt=use_advanced,
            prompt_version=version,
            use_few_shot=cfg.get("use_few_shot", use_advanced),
            use_domain_detection=cfg.get("use_domain_detection", False)
        )
    
    return _create_name_instance


def create_name():
    """Get CreateFolderNamer instance (backward compatibility)."""
    return get_create_name()