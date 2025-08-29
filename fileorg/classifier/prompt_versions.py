"""
Centralized Prompt Version Management for FileOrg Classifier

This module provides a single source of truth for all prompt versions,
ensuring backward compatibility and easy version management.

Key Features:
- All prompt versions in one place
- Easy to add new versions without breaking existing ones
- Clear feature flags for each version
- Simplified version switching
"""

from typing import Dict, Any, List

# Version 1: Legacy simple prompts
PROMPT_V1 = {
    "name": "Legacy Simple",
    "description": "Original simple classification prompts",
    "system": 'you are a master of categorizing content and give it a folder name in json format, eg. {"foldername": "/foldername"}',
    "prompt_prefix": "give me an appropriate folder name of the content must in json format:",
    "assistant_prefix": '{"foldername": "',
    "features": {
        "few_shot": False,
        "domain_detection": False,
        "remapping": False
    },
    "deprecated": False
}

# Version 2: Enhanced with guidelines
PROMPT_V2 = {
    "name": "Enhanced Classification",
    "description": "Detailed guidelines with category rules",
    "system": """You are an expert file organization assistant specializing in intelligent document classification.
        
Your task is to analyze content and assign it to the most appropriate folder category.
# IMPORTANT RULES
1. Your response MUST be ONLY the JSON object. Do not include any text before or after the JSON.
2. The `foldername` value MUST follow the `Category/Subcategory` format.
3. The `Category` and `Subcategory` names MUST be single, concise words or short phrases.
4. The entire `foldername` value MUST NOT exceed **20** characters.
5. If no suitable category is found, use "Uncategorized/Misc".

# Classification Guidelines:
1. Academic/Research → "Academic/{Subject}"
2. Business documents → "Business/{Type}"
3. Technical/Technology → "Technology/{Domain}"
4. Reports/Documentation → "Reports/{Category}"
5. Creative/Literature → "Creative/{Type}"
6. Health/Medical → "Health/{Category}"

Output format: {"foldername": "Category/Subcategory"}""",
    "prompt_prefix": "Based on the following content, determine the most appropriate folder category. Content: ",
    "assistant_prefix": '{"foldername": "',
    "features": {
        "few_shot": True,
        "domain_detection": True,
        "remapping": True
    },
    "deprecated": False,
    
    # Few-shot examples for v2
    "examples": [
        {
            "input": "Chapter 4: Principal Component Analysis - Mathematical foundations of PCA",
            "output": '{"foldername": "Academic/Statistics"}'
        },
        {
            "input": "Customer Order #ORD20250726-001 for Innovative Tech Co.",
            "output": '{"foldername": "Business/Orders"}'
        },
        {
            "input": "Excel Functions Reference Guide - VLOOKUP, SUMIF, INDEX-MATCH",
            "output": '{"foldername": "Technology/Spreadsheets"}'
        }
    ],
    
    # Remapping template for v2
    "remapping_system": """You are an expert at organizing and grouping related folder names.
Your task is to analyze a list of folder names and group similar ones together.

Grouping Rules:
1. Group folders with similar topics or domains
2. Create meaningful group names that encompass the folders
3. Maintain hierarchy when appropriate
4. Don't over-consolidate - keep distinct topics separate

Output format: [{"foldername": "original_name", "groupname": "consolidated_group"}, ...]""",
    "remapping_prefix": "Analyze and group these folder names intelligently: ",
    "remapping_assistant_prefix": '[{"foldername":"'
}

# Domain detection keywords (shared across versions that support it)
DOMAIN_KEYWORDS = {
    "Academic": ["chapter", "analysis", "study", "research", "principle", "theory", "exam"],
    "Business": ["order", "invoice", "customer", "payment", "contract", "budget"],
    "Technology": ["code", "software", "program", "algorithm", "ai", "machine learning"],
    "Creative": ["story", "stories", "novel", "fiction", "narrative"],
    "Health": ["health", "medical", "patient", "hospital", "clinic"]
}

# Master version registry
PROMPT_VERSIONS = {
    "v1": PROMPT_V1,
    "v2": PROMPT_V2
}

# Configuration
DEFAULT_VERSION = "v2"
SUPPORTED_VERSIONS = list(PROMPT_VERSIONS.keys())


def get_prompt_version(version: str = None) -> Dict[str, Any]:
    """
    Get a specific prompt version or the default.
    
    Args:
        version: Version string (e.g., 'v1', 'v2'). If None, uses DEFAULT_VERSION.
        
    Returns:
        Dictionary containing the prompt configuration for the specified version.
        
    Raises:
        ValueError: If the requested version doesn't exist.
    """
    if version is None:
        version = DEFAULT_VERSION
        
    if version not in PROMPT_VERSIONS:
        raise ValueError(
            f"Unknown prompt version: {version}. "
            f"Supported versions: {', '.join(SUPPORTED_VERSIONS)}"
        )
    
    return PROMPT_VERSIONS[version]


def get_version_features(version: str = None) -> Dict[str, bool]:
    """
    Get the feature flags for a specific version.
    
    Args:
        version: Version string. If None, uses DEFAULT_VERSION.
        
    Returns:
        Dictionary of feature flags and their boolean values.
    """
    prompt = get_prompt_version(version)
    return prompt.get("features", {})


def detect_domain(content: str) -> str:
    """
    Detect content domain based on keywords.
    
    Args:
        content: Text content to analyze.
        
    Returns:
        Detected domain name or "General" if no match.
    """
    content_lower = content.lower()
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in content_lower for keyword in keywords):
            return domain
    
    return "General"


def list_versions(include_deprecated: bool = False) -> List[str]:
    """
    List all available prompt versions.
    
    Args:
        include_deprecated: Whether to include deprecated versions.
        
    Returns:
        List of version strings.
    """
    versions = []
    for version, config in PROMPT_VERSIONS.items():
        if include_deprecated or not config.get("deprecated", False):
            versions.append(version)
    return versions


def migrate_config(old_config: Dict[str, Any]) -> str:
    """
    Helper to migrate from old config format to new version string.
    
    Args:
        old_config: Old configuration dictionary.
        
    Returns:
        Version string to use.
    """
    # Handle old classifier_version setting
    if "classifier_version" in old_config:
        return old_config["classifier_version"]
    
    # Handle old prompt_version setting  
    if "prompt_version" in old_config:
        return old_config["prompt_version"]
    
    # Default to v2 for backward compatibility
    return "v2" if old_config.get("use_advanced_prompt", False) else "v1"