"""Few-Shot Learning Examples for Enhanced Classification Accuracy.

This module provides carefully curated examples for few-shot learning,
helping LLMs understand classification patterns through concrete examples.
Examples are based on real-world document types and classification scenarios.

Key Features:
    - Domain-specific classification examples
    - Folder grouping and consolidation examples
    - Intelligent example selection based on content similarity
    - Formatted examples for direct prompt inclusion
"""

from typing import List, Dict, Any


class FewShotExamples:
    """Manages few-shot learning examples for improved LLM classification.
    
    This class provides a repository of curated examples that demonstrate
    correct classification patterns, helping LLMs learn from context and
    improve accuracy through few-shot learning.
    
    Class Attributes:
        CLASSIFICATION_EXAMPLES: List of document classification examples
            covering various domains (academic, business, technology, etc.)
        REMAPPING_EXAMPLES: List of folder grouping examples showing how
            to consolidate related folder names.
    """
    
    # Classification examples based on real test data
    CLASSIFICATION_EXAMPLES = [
        # Academic Examples
        {
            "input": "Chapter 4: Principal Component Analysis - This chapter covers the mathematical foundations of PCA including eigenvalues, eigenvectors, and dimensionality reduction techniques.",
            "output": '{"foldername": "Academic/Statistics"}',
            "explanation": "Academic content about statistical methods"
        },
        {
            "input": "CH04 Accounting Principles - Basic accounting equations, balance sheets, income statements, and financial analysis methods.",
            "output": '{"foldername": "Academic/Accounting"}',
            "explanation": "Academic content about accounting"
        },
        {
            "input": "Chapter 7: Cluster Analysis - Exploring k-means, hierarchical clustering, and DBSCAN algorithms for data grouping.",
            "output": '{"foldername": "Academic/DataScience"}',
            "explanation": "Academic content about data science methods"
        },
        
        # Business Examples
        {
            "input": "Customer Order #ORD20250726-001 for Innovative Tech Co., Ltd. Including 50x Intel i9 processors, delivery to Taiwan, payment terms 50% advance.",
            "output": '{"foldername": "Business/Orders"}',
            "explanation": "Business order document"
        },
        {
            "input": "Project ID 101: New Product Development - Budget $250,000, Team assignments, Task breakdown with deadlines and priorities.",
            "output": '{"foldername": "Business/Projects"}',
            "explanation": "Business project management document"
        },
        
        # Technology Examples
        {
            "input": "Excel Functions Reference Guide - VLOOKUP, SUMIF, INDEX-MATCH, Pivot Tables, and advanced formulas for data analysis.",
            "output": '{"foldername": "Technology/Spreadsheets"}',
            "explanation": "Technical documentation for Excel"
        },
        {
            "input": "Small Changes in AI: How incremental improvements in transformer architectures are revolutionizing NLP applications.",
            "output": '{"foldername": "Technology/AI"}',
            "explanation": "Technology presentation about AI"
        },
        
        # Health/Medical Examples
        {
            "input": "Health Organizations Directory - List of hospitals, clinics, and medical facilities with contact information and specializations.",
            "output": '{"foldername": "Health/Organizations"}',
            "explanation": "Health organization information"
        },
        
        # Creative/Literature Examples
        {
            "input": "Short Stories Collection - The Garden of Forking Paths, The Lottery, Hills Like White Elephants, and other classic narratives.",
            "output": '{"foldername": "Creative/Stories"}',
            "explanation": "Literature and creative writing"
        }
    ]
    
    # Remapping/Grouping examples
    REMAPPING_EXAMPLES = [
        {
            "input": ["Academic/Statistics", "Academic/Mathematics", "Academic/DataScience"],
            "output": [
                {"foldername": "Academic/Statistics", "groupname": "Academic/Quantitative"},
                {"foldername": "Academic/Mathematics", "groupname": "Academic/Quantitative"},
                {"foldername": "Academic/DataScience", "groupname": "Academic/Quantitative"}
            ],
            "explanation": "Group related academic subjects"
        },
        {
            "input": ["Business/Orders", "Business/Invoices", "Business/Contracts"],
            "output": [
                {"foldername": "Business/Orders", "groupname": "Business/Transactions"},
                {"foldername": "Business/Invoices", "groupname": "Business/Transactions"},
                {"foldername": "Business/Contracts", "groupname": "Business/Legal"}
            ],
            "explanation": "Group business documents by function"
        },
        {
            "input": ["Technology/AI", "Technology/MachineLearning", "Technology/DeepLearning"],
            "output": [
                {"foldername": "Technology/AI", "groupname": "Technology/AI"},
                {"foldername": "Technology/MachineLearning", "groupname": "Technology/AI"},
                {"foldername": "Technology/DeepLearning", "groupname": "Technology/AI"}
            ],
            "explanation": "Consolidate AI-related technologies"
        }
    ]
    
    @classmethod
    def get_examples(cls, example_type: str = "classification", count: int = 3) -> List[Dict]:
        """Retrieve a specified number of examples for few-shot learning.
        
        Args:
            example_type (str): Type of examples to retrieve. Options:
                - 'classification': Document classification examples
                - 'remapping': Folder grouping examples
                Defaults to 'classification'.
            count (int): Number of examples to return. More examples can
                improve accuracy but increase prompt length. Defaults to 3.
            
        Returns:
            List[Dict]: List of example dictionaries, each containing:
                - 'input': Example input text or data
                - 'output': Expected output/classification
                - 'explanation': Reasoning behind the classification
        
        Example:
            >>> examples = FewShotExamples.get_examples("classification", 2)
            >>> print(examples[0]['explanation'])
            "Academic content about statistical methods"
        """
        if example_type == "classification":
            return cls.CLASSIFICATION_EXAMPLES[:count]
        elif example_type == "remapping":
            return cls.REMAPPING_EXAMPLES[:count]
        return []
    
    @classmethod
    def format_for_prompt(cls, examples: List[Dict], example_type: str = "classification") -> str:
        """Format examples into a string suitable for prompt inclusion.
        
        Converts example dictionaries into a formatted string that can be
        directly inserted into prompts for few-shot learning.
        
        Args:
            examples (List[Dict]): List of example dictionaries to format.
            example_type (str): Type of examples being formatted.
                Affects formatting style. Defaults to 'classification'.
            
        Returns:
            str: Formatted string ready for prompt inclusion, with numbered
                examples and clear input/output pairs.
        
        Example:
            >>> examples = FewShotExamples.get_examples("classification", 2)
            >>> formatted = FewShotExamples.format_for_prompt(examples)
            >>> print(formatted[:30])
            "\n\nExamples:\n\nExample 1:\nInput:"
        """
        if not examples:
            return ""
        
        formatted = "\n\nExamples:\n"
        
        if example_type == "classification":
            for i, ex in enumerate(examples, 1):
                formatted += f"\nExample {i}:\n"
                formatted += f"Input: {ex['input'][:100]}...\n"
                formatted += f"Output: {ex['output']}\n"
        
        elif example_type == "remapping":
            for i, ex in enumerate(examples, 1):
                formatted += f"\nExample {i}:\n"
                formatted += f"Input: {ex['input']}\n"
                formatted += f"Output: {ex['output']}\n"
        
        return formatted
    
    @classmethod
    def get_relevant_examples(cls, content: str, count: int = 2) -> List[Dict]:
        """Select the most relevant examples based on content similarity.
        
        Uses keyword matching to find examples most similar to the input
        content, ensuring the LLM sees relevant classification patterns.
        
        Args:
            content (str): Input content to find similar examples for.
            count (int): Number of relevant examples to return.
                Defaults to 2.
            
        Returns:
            List[Dict]: Most relevant examples sorted by similarity score.
                Each example contains input, output, and explanation.
        
        Example:
            >>> content = "Chapter on statistical analysis and data science"
            >>> examples = FewShotExamples.get_relevant_examples(content, 2)
            >>> # Returns examples related to statistics and data science
        
        Note:
            Similarity is calculated based on keyword overlap between
            the input content and example text.
        """
        content_lower = content.lower()
        relevant = []
        
        # Score each example by keyword matching
        for example in cls.CLASSIFICATION_EXAMPLES:
            score = 0
            example_text = example["input"].lower()
            
            # Check for common keywords
            keywords = ["academic", "business", "technology", "health", "creative", 
                       "order", "customer", "chapter", "analysis", "excel", "ai"]
            
            for keyword in keywords:
                if keyword in content_lower and keyword in example_text:
                    score += 1
            
            relevant.append((score, example))
        
        # Sort by score and return top matches
        relevant.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in relevant[:count]]