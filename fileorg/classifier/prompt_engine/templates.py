"""Prompt Templates for Advanced File Classification.

This module provides versioned prompt templates for file classification
and folder organization tasks. Templates are carefully crafted to guide
LLMs in producing accurate and consistent classification results.

Key Features:
    - Multiple template versions for backward compatibility
    - Domain-specific classification guidelines
    - Hierarchical folder structure templates
    - Automatic domain detection based on content keywords

Template Versions:
    - v1: Legacy templates for backward compatibility
    - v2: Enhanced templates with detailed classification guidelines
"""

from typing import Dict


class PromptTemplates:
    """Manages prompt templates for file classification and organization.
    
    This class provides a centralized repository of prompt templates,
    supporting multiple versions and domain-specific variations for
    optimal classification accuracy.
    
    Class Attributes:
        LEGACY_CLASSIFICATION: Original v1 classification template
        CLASSIFICATION_V2: Enhanced v2 template with detailed guidelines
        REMAPPING_V2: Template for folder name grouping and consolidation
        ACADEMIC_TEMPLATE: Domain-specific template for academic content
        BUSINESS_TEMPLATE: Domain-specific template for business documents
    """
    
    # Legacy template (v1) - for backward compatibility
    LEGACY_CLASSIFICATION = {
        "system": 'you are a master of categorizing content and give it a folder name in json format, eg. {"foldername": "/foldername"}',
        "prompt_prefix": "give me an appropriate folder name of the content must in json format:",
        "assistant_prefix": '{"foldername": "'
    }
    
    # Enhanced template (v2) with better guidance
    CLASSIFICATION_V2 = {
        "system": """You are an expert file organization assistant specializing in intelligent document classification.
        
Your task is to analyze content and assign it to the most appropriate folder category.

Classification Guidelines:
1. Academic/Research documents → "Academic/{Subject}"
   - Papers, studies, analysis, coursework
   - Examples: "Academic/Mathematics", "Academic/ComputerScience", "Academic/Statistics"

2. Business documents → "Business/{Type}"
   - Orders, invoices, contracts, reports
   - Examples: "Business/Orders", "Business/Finance", "Business/Contracts"

3. Technical/Technology → "Technology/{Domain}"
   - Programming, AI, software, hardware docs
   - Examples: "Technology/AI", "Technology/Programming", "Technology/Excel"

4. Reports/Documentation → "Reports/{Category}"
   - General reports, documentation, guides
   - Examples: "Reports/Annual", "Reports/Technical", "Reports/UserGuides"

5. Creative/Literature → "Creative/{Type}"
   - Stories, articles, creative writing
   - Examples: "Creative/Stories", "Creative/Articles"

6. Health/Medical → "Health/{Category}"
   - Medical reports, health organizations
   - Examples: "Health/Organizations", "Health/Reports"

Output format: {"foldername": "Category/Subcategory"}
Be specific but not overly granular. Aim for 2-level hierarchy maximum.""",
        
        "prompt_prefix": "Based on the following content, determine the most appropriate folder category. Content: ",
        "assistant_prefix": '{"foldername": "'
    }
    
    # Remapping template for grouping related folders
    REMAPPING_V2 = {
        "system": """You are an expert at organizing and grouping related folder names.
        
Your task is to analyze a list of folder names and group similar or related ones together.

Grouping Rules:
1. Group folders with similar topics or domains
2. Create meaningful group names that encompass the folders
3. Maintain hierarchy when appropriate
4. Don't over-consolidate - keep distinct topics separate

Output format: [{"foldername": "original_name", "groupname": "consolidated_group"}, ...]

Examples:
- "Statistics", "Mathematics", "DataAnalysis" → group as "Academic"
- "CustomerOrders", "Invoices", "Contracts" → group as "Business"
- "PythonCode", "JavaScripts", "SQLQueries" → group as "Programming"
""",
        "prompt_prefix": "Analyze and group these folder names intelligently: ",
        "assistant_prefix": '[{"foldername":"'
    }
    
    # Domain-specific templates
    ACADEMIC_TEMPLATE = {
        "keywords": ["chapter", "analysis", "study", "research", "principle", "theory", "exam"],
        "default_category": "Academic",
        "subcategories": {
            "mathematics": ["statistics", "calculus", "algebra", "geometry"],
            "computer_science": ["algorithm", "programming", "software", "data structure"],
            "business": ["accounting", "finance", "management", "economics"]
        }
    }
    
    BUSINESS_TEMPLATE = {
        "keywords": ["order", "invoice", "customer", "payment", "contract", "budget"],
        "default_category": "Business",
        "subcategories": {
            "orders": ["purchase", "order", "requisition"],
            "finance": ["invoice", "payment", "budget", "accounting"],
            "contracts": ["agreement", "contract", "terms"]
        }
    }
    
    @classmethod
    def get_template(cls, version: str = "v2", template_type: str = "classification") -> Dict:
        """Retrieve a specific template by version and type.
        
        Args:
            version (str): Template version to retrieve. Options:
                - 'v1': Legacy templates for backward compatibility
                - 'v2': Enhanced templates with better guidance
                Defaults to 'v2'.
            template_type (str): Type of template needed. Options:
                - 'classification': For document classification tasks
                - 'remapping': For folder name grouping tasks
                Defaults to 'classification'.
            
        Returns:
            Dict: Template dictionary containing prompt components:
                - 'system': System message for LLM role definition
                - 'prompt_prefix': Prefix for user prompts
                - 'assistant_prefix': Prefix for assistant responses
        
        Example:
            >>> template = PromptTemplates.get_template("v2", "classification")
            >>> print(template['system'][:50])
            "You are an expert file organization assistant..."
        """
        if version == "v1":
            return cls.LEGACY_CLASSIFICATION
        elif version == "v2":
            if template_type == "classification":
                return cls.CLASSIFICATION_V2
            elif template_type == "remapping":
                return cls.REMAPPING_V2
        
        # Default fallback to legacy
        return cls.LEGACY_CLASSIFICATION
    
    @classmethod
    def detect_domain(cls, content: str) -> str:
        """Detect the content domain based on keyword analysis.
        
        Analyzes text content to identify its domain category by matching
        against predefined keyword sets for different domains.
        
        Args:
            content (str): Text content to analyze for domain detection.
            
        Returns:
            str: Detected domain name. Possible values:
                - 'Academic': Educational or research content
                - 'Business': Business documents and transactions
                - 'Technology': Technical or programming content
                - 'Creative': Creative writing or literature
                - 'Health': Medical or health-related content
                - 'General': Default when no specific domain detected
        
        Example:
            >>> domain = PromptTemplates.detect_domain("Chapter 4: Statistics")
            >>> print(domain)  # Output: "Academic"
        """
        content_lower = content.lower()
        
        # Check academic keywords
        if any(keyword in content_lower for keyword in cls.ACADEMIC_TEMPLATE["keywords"]):
            return "Academic"
        
        # Check business keywords  
        if any(keyword in content_lower for keyword in cls.BUSINESS_TEMPLATE["keywords"]):
            return "Business"
        
        # Check for technology/programming
        tech_keywords = ["code", "software", "program", "algorithm", "ai", "machine learning"]
        if any(keyword in content_lower for keyword in tech_keywords):
            return "Technology"
        
        # Check for creative content
        creative_keywords = ["story", "stories", "novel", "fiction", "narrative"]
        if any(keyword in content_lower for keyword in creative_keywords):
            return "Creative"
        
        # Check for health/medical
        health_keywords = ["health", "medical", "patient", "hospital", "clinic"]
        if any(keyword in content_lower for keyword in health_keywords):
            return "Health"
        
        return "General"