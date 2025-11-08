"""
LLM Classifier Ports - Business-Agnostic Interfaces

Defines contracts for LLM-based text classification independent of specific use cases.
Focus: Text input/output handling and model constraints.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    import jinja2

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
    Prompt engineering interface for constructing LLM messages.

    This interface defines HOW to build prompts from input text and instructions.
    Different implementations can use different strategies:
    - Template-based prompts (LlamaPromptBuilder using ITemplateLoader)
    - Hardcoded prompts (for simple use cases)
    - Dynamic prompts based on context

    Relationship with ITemplateLoader:
        IPromptBuilder and ITemplateLoader are separate concerns:
        - IPromptBuilder: WHAT messages to send to the LLM (prompt construction logic)
        - ITemplateLoader: HOW to retrieve template content (I/O and caching)

        This separation follows composition over inheritance:
        - Template-based builders compose ITemplateLoader for flexible prompt management
        - This is NOT redundant - it's clean architecture with clear boundaries

    Usage:
        # Template-based approach (recommended for production)
        loader = Jinja2TemplateLoader(base_path="prompts/")
        builder = LlamaPromptBuilder(
            template_loader=loader,
            provider="llama3b",
            version="v1"
        )
        messages = builder.build_prompt(text="classify this", instruction="...")

    Current Implementation:
        - LlamaPromptBuilder: Jinja2 templates with version control, composes ITemplateLoader
          Supports Llama 3B/8B with provider-specific optimizations and A/B testing via versions
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
            Chat-formatted messages for LLM, e.g.:
            [
                {"role": "system", "content": "You are a classifier..."},
                {"role": "user", "content": "Classify this text..."}
            ]
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


class ITemplateLoader(ABC):
    """
    Load and cache prompt templates from storage (filesystem, database, etc.).

    Usage:
        # Standalone usage
        loader = Jinja2TemplateLoader(base_path="prompts/")
        template = loader.load_template(provider="llama3b", version="v1", template_type="system")
        content = template.render(suggested_categories=["doc", "code"])

        # Composed with IPromptBuilder
        loader = Jinja2TemplateLoader(base_path="prompts/")
        builder = LlamaPromptBuilder(template_loader=loader, provider="llama3b", version="v1")
        messages = builder.build_prompt(text="...", instruction="...")

    Implementations:
        - Jinja2TemplateLoader: Filesystem-based with LRU caching
    """

    @abstractmethod
    def load_template(self, provider: str, version: str, template_type: str) -> "jinja2.Template":
        """
        Load a specific template with caching.

        Args:
            provider: LLM provider name (e.g., "llama3b", "llama8b")
            version: Template version (e.g., "v1", "v2") for A/B testing
            template_type: Type of template (e.g., "system", "user")

        Returns:
            Jinja2 Template object ready for rendering

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If template is invalid or has syntax errors
        """
        pass

    @abstractmethod
    def template_exists(self, provider: str, version: str, template_type: str) -> bool:
        """
        Check if a template exists without loading it.

        Useful for validation and graceful degradation.

        Args:
            provider: LLM provider name
            version: Template version
            template_type: Type of template

        Returns:
            True if template exists and is accessible, False otherwise
        """
        pass
