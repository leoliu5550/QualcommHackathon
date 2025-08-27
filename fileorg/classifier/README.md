# Folder Namer - Prompt Engineering Module

## 🚀 Quick Start
```python
# v1 (Legacy) - 簡單直接
namer = CreateFolderNamer()

# v2 (Advanced) - 智能優化
namer = CreateFolderNamer(
    use_advanced_prompt=True,
    prompt_version="v2",
    use_few_shot=True,
    use_domain_detection=True
)
```

## 📊 執行流程

### 分類流程優化 (v1 → v2)
```
v1: 內容 → Prompt → LLM → 輸出
v2: 內容 → 優化 → 領域偵測 → Few-shot → Prompt → LLM → 驗證 → 輸出
```

### 關鍵改進
- **內容優化**: 移除雜訊，保留關鍵資訊 (500字元限制)
- **領域偵測**: 自動識別 Academic/Business/Technology 等類別
- **Few-shot Learning**: 提供相關範例提升準確度
- **輸出驗證**: 自動修復 JSON 格式錯誤

## 🔧 新增 v3 版本指南

### 1. 新增模板 (`templates.py`)
```python
class PromptTemplates:
    # 新增 v3 模板
    CLASSIFICATION_V3 = {
        "system": "你的新系統提示詞...",
        "prompt_prefix": "...",
        "assistant_prefix": "..."
    }
    
    @classmethod
    def get_template(cls, version, template_type):
        # 加入 v3 判斷
        elif version == "v3":
            if template_type == "classification":
                return cls.CLASSIFICATION_V3
```

### 2. 更新建構器 (`builder.py`)
```python
# 在 build_classification_prompt 中加入 v3 邏輯
if self.version == "v3":
    # 實作 v3 特有的 prompt 建構邏輯
    messages = self._build_v3_messages(content)
```

### 3. 調整主程式 (`folder_namer_v2.py`)
```python
# __init__ 中允許 v3
self.prompt_version = prompt_version if prompt_version in ["v1", "v2", "v3"] else "v1"
```

## 📁 檔案說明

```
prompt_engine/
├── templates.py    # 模板定義 (新增版本在此)
├── builder.py      # Prompt 建構邏輯
├── optimizer.py    # 內容優化與驗證
└── examples.py     # Few-shot 範例庫
```

### 維護
1. **templates.py** - 新增/調整分類規則
2. **examples.py** - 更新 Few-shot 範例
3. **optimizer.py** - 調整內容優化策略