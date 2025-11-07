"""
LLM Classifier Ports - Business-Agnostic Interfaces

Defines contracts for LLM-based text classification independent of specific use cases.
Focus: Text input/output handling and model constraints.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

# ============================================================================
# Input/Output Data Models
# ============================================================================


@dataclass
class LLMInput:
    """
    Text input for LLM processing.

    Usage:
        input = LLMInput(text="content", max_tokens=150000)
        result = llm.classify(input)

    Args:
        text: Input text content
        max_tokens: Token limit (model-dependent, not business logic)
    """

    text: str
    max_tokens: int = 150000


@dataclass
class ClassificationOutput:
    """
    Classification result mapping classes to items.

    Structure: {class_name: [item1, item2, ...], ...}

    Usage:
        output = ClassificationOutput(
            classifications={"documents": ["file1.txt", "file2.pdf"]},
            raw_response="..."
        )

    Args:
        classifications: Dict mapping class names to lists of classified items
        raw_response: Original LLM text output (for debugging/logging)
        metadata: Optional metadata (confidence scores, etc.)
    """

    classifications: Dict[str, List[str]]
    raw_response: str
    metadata: Optional[Dict[str, float]] = None


# ============================================================================
# Inbound Ports - Use Cases
# ============================================================================


class IClassifierUseCase(ABC):
    """
    Text classification use case.

    Usage:
        classifier = MyClassifier()
        output = classifier.classify(LLMInput(text="..."))
        print(output.classifications)  # {"class_name": ["item1", ...]}
    """

    @abstractmethod
    def classify(self, input_data: LLMInput) -> ClassificationOutput:
        """
        Classify text input into categories.

        Args:
            input_data: Text input with token constraints

        Returns:
            Classification mapping {class_name: [items]}
        """
        pass


# ============================================================================
# Outbound Ports - External Dependencies
# ============================================================================


class ILLMProvider(ABC):
    """
    LLM inference provider (backend-agnostic).

    Usage:
        llm = QualcommLLM(api_key="...")
        response = llm.generate(messages=[{"role": "user", "content": "..."}])

    Implementations: Qualcomm NPU, HuggingFace, OpenAI, etc.
    """

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], max_tokens: int = 32768) -> str:
        """
        Generate text from LLM.

        Args:
            messages: Chat format - [{"role": "user/system", "content": "..."}]
            max_tokens: Generation token limit

        Returns:
            Generated text string
        """
        pass


class IPromptBuilder(ABC):
    """
    Prompt engineering interface.

    Usage:
        builder = MyPromptBuilder()
        messages = builder.build_prompt(text="classify this", instruction="...")
    """

    @abstractmethod
    def build_prompt(self, text: str, instruction: str, max_tokens: int = 150000) -> List[Dict[str, str]]:
        """
        Build LLM prompt from text and instruction.

        Args:
            text: Input text to process
            instruction: Task instruction (e.g., "classify into categories")
            max_tokens: Token limit for input text

        Returns:
            Chat-formatted messages for LLM
        """
        pass


class IOutputParser(ABC):
    """
    Parse LLM text output into structured format.

    Usage:
        parser = JSONOutputParser()
        result = parser.parse(llm_response)
        print(result)  # {"class_name": ["item1", "item2"]}
    """

    @abstractmethod
    def parse(self, text: str) -> Dict[str, List[str]]:
        """
        Parse LLM output to {class_name: [items]} format.

        Args:
            text: Raw LLM text output

        Returns:
            Dict mapping class names to item lists

        Raises:
            ValueError: If parsing fails
        """
        pass


class ITextValidator(ABC):
    """
    Validate and sanitize text outputs.

    Usage:
        validator = FileNameValidator()
        safe_name = validator.sanitize("unsafe/name?")  # "unsafe_name"
    """

    @abstractmethod
    def sanitize(self, text: str) -> str:
        """
        Sanitize text for safe usage (filesystem, display, etc.).

        Args:
            text: Raw text to sanitize

        Returns:
            Sanitized text
        """
        pass

    @abstractmethod
    def validate(self, text: str) -> bool:
        """
        Check if text is valid (non-empty, proper format, etc.).

        Args:
            text: Text to validate

        Returns:
            True if valid, False otherwise
        """
        pass
