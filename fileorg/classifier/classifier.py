"""Enhanced Folder Naming Tool with Prompt Engineering Support.

This module extends the original folder_namer.py with advanced prompt engineering capabilities
while maintaining full backward compatibility.

Key Features:
    - Advanced prompt engineering for better classification accuracy
    - Multiple prompt template versions (v1 for legacy, v2 for enhanced)
    - Few-shot learning support for improved context understanding
    - Automatic domain detection for specialized classification
    - Content optimization for more efficient LLM processing
    - Output validation and automatic error correction

Example:
    Basic usage (backward compatible)::

        from fileorg.classifier.folder_namer_v2 import CreateFolderNamer
        
        namer = CreateFolderNamer()
        folder_name = namer.create_folder_name("Document content here...")
        
    Advanced usage with prompt engineering::
    
        namer = CreateFolderNamer(
            use_advanced_prompt=True,
            prompt_version="v2",
            use_few_shot=True,
            use_domain_detection=True
        )
        folder_name = namer.create_folder_name("Document content here...")

"""

from typing import List, Dict, Any
import json
import re
import os

from fileorg.ai.interface import get_llm
from fileorg.ai.config import config


class CreateFolderNamer:
    """Enhanced folder naming tool with optional prompt engineering support.
    
    This class provides intelligent document classification and folder naming capabilities.
    It's fully backward compatible with the original implementation while offering
    advanced prompt engineering features for improved accuracy.
    
    Attributes:
        llm: The language model interface for inference.
        use_advanced_prompt (bool): Whether to use advanced prompt engineering.
        prompt_version (str): Version of prompt templates to use ('v1' or 'v2').
        use_few_shot (bool): Whether to include few-shot examples in prompts.
        use_domain_detection (bool): Whether to automatically detect content domain.
        prompt_builder: Instance of PromptBuilder for advanced prompt construction.
        prompt_optimizer: Instance of PromptOptimizer for content and output optimization.
    """
    
    def __init__(self, use_advanced_prompt: bool = False, prompt_version: str = "v1",
                 use_few_shot: bool = False, use_domain_detection: bool = False):
        """Initialize the folder naming tool with optional advanced features.
        
        Args:
            use_advanced_prompt (bool): Enable advanced prompt engineering features.
                Defaults to False for backward compatibility.
            prompt_version (str): Prompt template version to use. Options are 'v1' 
                (legacy) or 'v2' (enhanced with better guidance). Defaults to 'v1'.
            use_few_shot (bool): Include few-shot learning examples in prompts to
                improve classification accuracy. Only works when use_advanced_prompt=True.
                Defaults to False.
            use_domain_detection (bool): Automatically detect content domain (academic,
                business, technology, etc.) for specialized classification. Only works
                when use_advanced_prompt=True. Defaults to False.
        
        Note:
            The tool defaults to legacy mode for backward compatibility. To enable
            advanced features, set use_advanced_prompt=True.
        """
        self.llm = get_llm(
            backend=config.get("backend"),
            model_id=config.get("model_id"),
        )
        
        # 為了相容舊版，預設都是關閉的
        self.use_advanced_prompt = use_advanced_prompt
        self.prompt_version = prompt_version if use_advanced_prompt else "v1"
        self.use_few_shot = use_few_shot and use_advanced_prompt
        self.use_domain_detection = use_domain_detection and use_advanced_prompt
        
        # 只有在開啟進階功能時才引入相關模組
        if self.use_advanced_prompt:
            try:
                from .prompt_engine import PromptBuilder, PromptOptimizer
                self.prompt_builder = PromptBuilder(
                    version=self.prompt_version,
                    use_few_shot=self.use_few_shot,
                    use_domain_detection=self.use_domain_detection
                )
                self.prompt_optimizer = PromptOptimizer()
            except ImportError:
                print("提醒：找不到 prompt_engine 模組，自動切換回傳統模式")
                self.use_advanced_prompt = False
                self.prompt_builder = None
                self.prompt_optimizer = None
        else:
            self.prompt_builder = None
            self.prompt_optimizer = None
    
    def create_folder_name(self, content: str) -> str:
        """Generate an appropriate folder name for given file content.
        
        This method analyzes the provided content and generates a suitable folder name
        for classification. It uses either legacy or advanced prompt engineering based
        on the instance configuration.
        
        Args:
            content (str): The file content to classify. Can be partial content
                (e.g., first 500 characters) for efficiency.
        
        Returns:
            str: The generated folder name in format '/foldername'. The name is
                cleaned to contain only alphanumeric characters, Chinese characters,
                spaces, and forward slashes.
        
        Example:
            >>> namer = CreateFolderNamer()
            >>> content = "Chapter 4: Statistical Analysis of Data..."
            >>> folder = namer.create_folder_name(content)
            >>> print(folder)  # Output: "Academic/Statistics"
        """
        if self.use_advanced_prompt and self.prompt_builder:
            # 先優化內容（如果有 optimizer）
            if self.prompt_optimizer:
                content = self.prompt_optimizer.optimize_content(content, max_length=500)
            
            # 使用進階的提示詞建構方式
            messages = self.prompt_builder.build_classification_prompt(content)
        else:
            # 使用傳統提示詞（相容舊版）
            messages = self._build_legacy_classification_prompt(content)
        
        # 呼叫大型語言模型
        create_folder = self.llm.inference(prompt=messages, max_new_tokens=200)
        
        # 驗證並清理輸出結果
        if self.use_advanced_prompt and self.prompt_optimizer:
            is_valid, fixed_output = self.prompt_optimizer.validate_output(create_folder, "json")
            if is_valid:
                create_folder = fixed_output
        
        return self.clean_output(create_folder)
    
    def _build_legacy_classification_prompt(self, content: str) -> List[Dict[str, str]]:
        """Build legacy format prompt for backward compatibility.
        
        This private method constructs the traditional prompt format used in the
        original implementation.
        
        Args:
            content (str): Content to classify.
            
        Returns:
            List[Dict[str, str]]: List of message dictionaries in the format
                expected by the LLM interface. Each dictionary contains 'role'
                and 'content' keys.
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
        return messages
    
    def remapping_folder(self, candidate_folder: List[str]) -> List[Dict[str, str]]:
        """Group similar folder names together for better organization.
        
        This method analyzes a list of folder names and groups semantically similar
        ones together, reducing redundancy in the folder structure.
        
        Args:
            candidate_folder (List[str]): List of folder names to be grouped.
                Example: ["Statistics", "Mathematics", "DataAnalysis", "Orders"]
        
        Returns:
            List[Dict[str, str]]: List of mappings from original folder names to
                consolidated group names. Each dictionary contains:
                - 'foldername': Original folder name
                - 'groupname': Consolidated group name it should be mapped to
        
        Example:
            >>> namer = CreateFolderNamer()
            >>> folders = ["Statistics", "Mathematics", "DataAnalysis"]
            >>> mapping = namer.remapping_folder(folders)
            >>> print(mapping)
            [
                {"foldername": "Statistics", "groupname": "Academic"},
                {"foldername": "Mathematics", "groupname": "Academic"},
                {"foldername": "DataAnalysis", "groupname": "Academic"}
            ]
        """
        if self.use_advanced_prompt and self.prompt_builder:
            # 如果可以的話，先優化資料夾名稱
            if self.prompt_optimizer:
                candidate_folder = self.prompt_optimizer.optimize_folder_names(candidate_folder)
            
            # 使用進階的提示詞建構方式
            messages = self.prompt_builder.build_remapping_prompt(candidate_folder)
        else:
            # 使用傳統提示詞（相容舊版）
            messages = self._build_legacy_remapping_prompt(candidate_folder)
        
        # 進行推論（可以自行選擇 generate 或 pipeline 方式）
        mapp_folder = self.llm.inference(prompt=messages, max_new_tokens=400)
        
        # 解析並驗證輸出結果
        try:
            # 試著解析 JSON，如果出錯就手動修復看看
            if self.use_advanced_prompt and self.prompt_optimizer:
                is_valid, fixed_output = self.prompt_optimizer.validate_output(mapp_folder, "json")
                if is_valid:
                    mapp_folder = fixed_output
            
            # 傳統的 JSON 修復方式
            if not mapp_folder.startswith('['):
                mapp_folder = '[{"foldername":"' + mapp_folder
            if not mapp_folder.endswith(']'):
                mapp_folder = mapp_folder.rstrip(',') + ']'
            
            data = json.loads(mapp_folder)
        except json.JSONDecodeError as e:
            print(f"JSON 解析失敗了: {e}\n輸出內容: {mapp_folder}")
            # 如果 JSON 解析失敗，就用原本的對應關係
            data = [{"foldername": folder, "groupname": folder} for folder in candidate_folder]
        
        # 清理資料夾名稱與群組名稱
        for item in data:
            item["foldername"] = item["foldername"].lstrip('/')
            item["groupname"] = self.clean_output(item["groupname"])
        
        return data
    
    def _build_legacy_remapping_prompt(self, candidate_folder: List[str]) -> List[Dict[str, str]]:
        """Build legacy format remapping prompt for backward compatibility.
        
        This private method constructs the traditional prompt format for folder
        grouping used in the original implementation.
        
        Args:
            candidate_folder (List[str]): List of folder names to group.
            
        Returns:
            List[Dict[str, str]]: List of message dictionaries in the format
                expected by the LLM interface.
        """
        pmt = "categorize the foldername into several groups if they are related or similar and give each group a name, must in json format:"
        txt = "[" + ", ".join(candidate_folder) + "]"
        cnt = pmt + txt
        messages = [
            {"role": "system", "content": 'you are a master of categorizing folder names and give it a new group name in json format, eg. {"foldername":"/foldername", "groupname":"/groupname"]}'},
            {"role": "user", "content": cnt},
            {"role": "assistant", "content": '{"groups": ["'},
        ]
        return messages
    
    def clean_output(self, text: str) -> str:
        """Clean and sanitize output text from LLM.
        
        Removes unwanted characters while preserving Chinese characters, English
        letters, digits, and spaces. Removes forward slashes for path safety.
        
        Args:
            text (str): Raw text output from LLM.
            
        Returns:
            str: Cleaned text suitable for use as a folder name.
        """
        # 保留中文、英文大小寫與阿拉伯數字、空格，其餘全部移除（包括斜線）
        cleaned = re.sub(r'[^\u4e00-\u9fa5A-Za-z0-9\s]', '', text)
        return cleaned.strip()
    
    def process_files(self, summaries_data: Dict[str, Any], base_output_dir: str = "./") -> Dict[str, List[Dict[str, str]]]:
        """Process files and generate organized folder structure.
        
        This is the main processing method that integrates all classification and
        grouping steps to organize files into a meaningful folder structure.
        
        Args:
            summaries_data (Dict[str, Any]): Dictionary containing a 'summaries' list.
                Each summary item should have:
                - 'summary': Text content to classify
                - 'path': Original file path
                - 'name': File name
            base_output_dir (str): Base directory for output file organization.
                Defaults to current directory './'.
        
        Returns:
            Dict[str, List[Dict[str, str]]]: Dictionary with 'file_paths' key containing
                a list of file mappings. Each mapping has:
                - 'original': Original file path
                - 'new': New organized file path
        
        Example:
            >>> data = {
            ...     "summaries": [
            ...         {"summary": "Statistics chapter...", "path": "/old/stat.txt", "name": "stat.txt"},
            ...         {"summary": "Math problems...", "path": "/old/math.txt", "name": "math.txt"}
            ...     ]
            ... }
            >>> result = namer.process_files(data, "/organized/")
            >>> print(result)
            {
                "file_paths": [
                    {"original": "/old/stat.txt", "new": "/organized/Academic/stat.txt"},
                    {"original": "/old/math.txt", "new": "/organized/Academic/math.txt"}
                ]
            }
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
        """Save processing results to a JSON file.
        
        Args:
            result (Dict[str, Any]): Results dictionary containing file mappings.
            output_file (str): Path to output JSON file. Defaults to 'file_mapping_result.json'.
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"結果已儲存到: {output_file}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get prompt optimization statistics if advanced features are enabled.
        
        Returns:
            Dict[str, Any]: Dictionary containing optimization statistics such as:
                - 'total_optimized': Number of optimizations performed
                - 'avg_length_reduction': Average content length reduction
                - 'improvements': List of optimization improvements
                Returns empty dictionary if advanced features are disabled.
        """
        if self.use_advanced_prompt and self.prompt_optimizer:
            return self.prompt_optimizer.get_optimization_stats()
        return {}


# Singleton pattern for model state management
_create_name_instance = None


def get_create_name():
    """Get or create the singleton CreateFolderNamer instance.
    
    This lazy initialization prevents model loading during import,
    which is especially important for testing.
    
    Returns:
        CreateFolderNamer: Singleton instance with v2 features enabled by default
    """
    global _create_name_instance
    if _create_name_instance is None:
        # Default to v2 with enhanced features
        from fileorg.ai.config import Config
        cfg = Config()
        
        # Check if config specifies to use v1
        use_v2 = cfg.get("classifier_version", "v2") == "v2"
        
        if use_v2:
            # Use v2 with advanced features
            _create_name_instance = CreateFolderNamer(
                use_advanced_prompt=True,
                prompt_version="v2",
                use_few_shot=cfg.get("use_few_shot", True),
                use_domain_detection=cfg.get("use_domain_detection", False)
            )
        else:
            # Fallback to v1 compatibility mode
            _create_name_instance = CreateFolderNamer(use_advanced_prompt=False)
    
    return _create_name_instance


# For backward compatibility - create_name is a function that returns the instance
def create_name():
    """Backward compatible function interface.
    
    Returns the singleton instance for use in existing code.
    """
    return get_create_name()