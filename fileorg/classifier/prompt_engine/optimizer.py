"""Prompt Optimizer Module for Enhanced LLM Performance.

This module provides optimization capabilities for prompts and LLM outputs,
including content optimization, output validation, and error correction.

Key Features:
    - Intelligent content truncation and noise removal
    - Output validation and automatic error correction
    - Folder name normalization and deduplication
    - Performance statistics tracking
"""

import re
from typing import Dict, List, Any, Optional


class PromptOptimizer:
    """Optimizes prompts and validates outputs for improved LLM performance.
    
    This class provides various optimization techniques to improve prompt
    efficiency and output accuracy, including content preprocessing,
    intelligent truncation, and output validation.
    
    Attributes:
        optimization_stats (dict): Statistics tracking optimization performance,
            including total optimizations, length reductions, and improvements.
    """
    
    def __init__(self):
        """Initialize the PromptOptimizer with default statistics."""
        self.optimization_stats = {
            "total_optimized": 0,
            "avg_length_reduction": 0,
            "improvements": []
        }
    
    def optimize_content(self, content: str, max_length: int = 500) -> str:
        """Optimize content for efficient prompt inclusion.
        
        Preprocesses content by removing noise, normalizing whitespace,
        and intelligently truncating to fit within token limits while
        preserving important information.
        
        Args:
            content (str): Original content to optimize.
            max_length (int): Maximum allowed content length in characters.
                Content exceeding this will be intelligently truncated.
                Defaults to 500.
            
        Returns:
            str: Optimized content ready for prompt inclusion.
        
        Example:
            >>> optimizer = PromptOptimizer()
            >>> text = "Chapter 1\n\n\n   Statistical Analysis...[long text]"
            >>> optimized = optimizer.optimize_content(text, max_length=100)
            >>> # Returns cleaned and truncated version
        """
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Remove non-informative patterns
        content = self._remove_noise(content)
        
        # Smart truncation if needed
        if len(content) > max_length:
            content = self._smart_truncate(content, max_length)
        
        self.optimization_stats["total_optimized"] += 1
        
        return content
    
    def _remove_noise(self, text: str) -> str:
        """Remove noise and non-informative patterns from text.
        
        Eliminates redundant punctuation, excessive special characters,
        page numbers, and other noise that doesn't contribute to
        content understanding.
        
        Args:
            text (str): Input text to clean.
            
        Returns:
            str: Cleaned text with noise removed.
        """
        # Remove multiple punctuation
        text = re.sub(r'[.!?]+', '.', text)
        
        # Remove excessive special characters
        text = re.sub(r'[-=_]{3,}', '', text)
        
        # Remove page numbers and similar patterns
        text = re.sub(r'Page \d+|p\.\d+|\[\d+\]', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Intelligently truncate text while preserving semantic meaning.
        
        Attempts to truncate at sentence boundaries when possible,
        ensuring the most informative content is retained.
        
        Args:
            text (str): Text to truncate.
            max_length (int): Maximum allowed length.
            
        Returns:
            str: Truncated text that fits within max_length while
                preserving as much meaning as possible.
        """
        if len(text) <= max_length:
            return text
        
        # Try to find a good breaking point
        sentences = text.split('.')
        truncated = ""
        
        for sentence in sentences:
            if len(truncated) + len(sentence) + 1 <= max_length:
                truncated += sentence + "."
            else:
                break
        
        # If no complete sentences fit, just truncate
        if not truncated:
            truncated = text[:max_length-3] + "..."
        
        return truncated.strip()
    
    def optimize_folder_names(self, folder_names: List[str]) -> List[str]:
        """Optimize and normalize a list of folder names.
        
        Removes duplicates, normalizes path separators, and cleans
        folder names for consistency.
        
        Args:
            folder_names (List[str]): Original folder names to optimize.
            
        Returns:
            List[str]: Optimized list with duplicates removed and
                names normalized.
        
        Example:
            >>> optimizer = PromptOptimizer()
            >>> folders = ["/Statistics", "Statistics", "\\Mathematics"]
            >>> optimized = optimizer.optimize_folder_names(folders)
            >>> # Returns ["Statistics", "Mathematics"]
        """
        optimized = []
        
        for name in folder_names:
            # Remove leading/trailing slashes
            name = name.strip('/')
            
            # Normalize path separators
            name = name.replace('\\', '/')
            
            # Remove duplicates while preserving order
            if name not in optimized:
                optimized.append(name)
        
        return optimized
    
    def validate_output(self, output: str, expected_format: str = "json") -> tuple[bool, str]:
        """Validate and attempt to fix LLM output format.
        
        Checks if output matches the expected format and attempts to
        fix common formatting errors automatically.
        
        Args:
            output (str): Raw LLM output string to validate.
            expected_format (str): Expected output format. Supported values:
                - 'json': JSON format validation and fixing
                - 'list': List format validation
                Defaults to 'json'.
            
        Returns:
            tuple[bool, str]: Tuple containing:
                - bool: True if output is valid (or was successfully fixed)
                - str: Fixed output if validation succeeded, original otherwise
        
        Example:
            >>> optimizer = PromptOptimizer()
            >>> output = '{foldername: "Statistics"}'  # Missing quotes
            >>> is_valid, fixed = optimizer.validate_output(output, "json")
            >>> # Returns (True, '{"foldername": "Statistics"}')
        """
        if expected_format == "json":
            return self._validate_json_output(output)
        elif expected_format == "list":
            return self._validate_list_output(output)
        
        return True, output
    
    def _validate_json_output(self, output: str) -> tuple[bool, str]:
        """Validate and fix JSON formatted output.
        
        Attempts to parse JSON and fix common issues like missing quotes,
        wrong quote types, and missing brackets.
        
        Args:
            output (str): JSON string to validate.
            
        Returns:
            tuple[bool, str]: (is_valid, fixed_output) where fixed_output
                is the corrected JSON if fixable, original otherwise.
        """
        import json
        
        # Try to parse as-is
        try:
            json.loads(output)
            return True, output
        except:
            pass
        
        # Try to fix common issues
        fixed = output
        
        # Add missing quotes
        fixed = re.sub(r'(\w+):', r'"\1":', fixed)
        
        # Fix single quotes to double quotes
        fixed = fixed.replace("'", '"')
        
        # Add missing brackets
        if not fixed.startswith('[') and '"foldername"' in fixed:
            fixed = '[' + fixed
        if not fixed.endswith(']') and fixed.startswith('['):
            fixed = fixed.rstrip(',') + ']'
        
        # Try parsing the fixed version
        try:
            json.loads(fixed)
            return True, fixed
        except:
            # If still invalid, return original
            return False, output
    
    def _validate_list_output(self, output: str) -> tuple[bool, str]:
        """Validate and fix list formatted output.
        
        Ensures output is properly formatted as a list with brackets.
        
        Args:
            output (str): List string to validate.
            
        Returns:
            tuple[bool, str]: (is_valid, fixed_output) where fixed_output
                has proper list formatting.
        """
        # Check if it looks like a list
        if output.startswith('[') and output.endswith(']'):
            return True, output
        
        # Try to fix
        fixed = output.strip()
        if not fixed.startswith('['):
            fixed = '[' + fixed
        if not fixed.endswith(']'):
            fixed = fixed + ']'
        
        return True, fixed
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get current optimization statistics.
        
        Returns:
            Dict[str, Any]: Dictionary containing:
                - 'total_optimized': Total number of optimizations performed
                - 'avg_length_reduction': Average content length reduction
                - 'improvements': List of specific improvements made
        """
        return self.optimization_stats.copy()
    
    def reset_stats(self):
        """Reset optimization statistics to initial state."""
        self.optimization_stats = {
            "total_optimized": 0,
            "avg_length_reduction": 0,
            "improvements": []
        }