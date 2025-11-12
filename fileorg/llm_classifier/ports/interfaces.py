"""
LLM Classifier Interfaces - Port Definitions
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    import jinja2

    from .models import ClassificationOutput, FileMapping, FileSummary, LLMInput


class IClassifierUseCase(ABC):
    """
    Text classification use case interface.

    Usage:
        classifier = FileClassifier(llm_provider=..., prompt_builder=...)
        output = classifier.classify(LLMInput(text="..."))
        print(output.classifications)  # {"class_name": ["item1", ...]}
    """

    @abstractmethod
    def classify(self, input_data: "LLMInput") -> "ClassificationOutput":
        """
        Classify text input into categories.

        Args:
            input_data: Text input with token constraints

        Returns:
            Classification mapping {class_name: [items]}
        """
        pass


class ILLMProvider(ABC):
    """
    LLM inference provider interface (Outbound Port).

    Usage:
        llm = HuggingFaceProvider(model_name="meta-llama/Llama-3.2-3B-Instruct")
        response = llm.generate(messages=[{"role": "user", "content": "..."}])
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
    Prompt construction strategy interface (Application Strategy).

    Relationship with ITemplateLoader:
        - IPromptBuilder: Application strategy - HOW to construct prompts (business logic)
        - ITemplateLoader: Infrastructure port - WHERE to get template content (I/O)

    Usage:
        # Template-based approach (recommended)
        loader = Jinja2TemplateLoader(base_path="prompts/")  # Adapter
        builder = LlamaPromptBuilder(                        # Use Case strategy
            template_loader=loader,
            provider="llama3b",
            version="v1"
        )
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
            Chat-formatted messages for LLM, e.g.:
            [
                {"role": "system", "content": "You are a classifier..."},
                {"role": "user", "content": "Classify this text..."}
            ]
        """
        pass


class ISummaryParser(ABC):
    """
    Summary parsing strategy interface for Stage 1 (Application Strategy).

    Parses LLM output from Stage 1 summarization to create FileSummary objects.
    This interface is separate from IOutputParser because Stage 1 has different
    responsibilities and return types than Stage 2.

    Usage:
        parser = SummaryOutputParser()
        result = parser.parse(llm_response, file_path="/path/to/file.txt")
        # Returns: FileSummary(file_path="...", summary="folder name", ...)
    """

    @abstractmethod
    def parse(
        self,
        text: str,
        file_path: Optional[str] = None,
        raw_length: Optional[int] = None,
    ) -> "FileSummary":
        """
        Parse LLM output to FileSummary object.

        Args:
            text: Raw LLM text output
            file_path: File path for the summary
            raw_length: Optional length of raw response for metadata

        Returns:
            FileSummary object containing file path and folder name

        Raises:
            ValueError: If parsing fails
        """
        pass


class IOutputParser(ABC):
    """
    LLM output parsing strategy interface (Application Strategy).

    Parses LLM output to file path mappings.

    Usage:
        parser = PathMappingOutputParser()
        result = parser.parse(llm_response)
        # Returns: {"C:/old/path": FileMapping(...)}
    """

    @abstractmethod
    def parse(self, text: str) -> Dict[str, "FileMapping"]:
        """
        Parse LLM output to path mappings.

        Args:
            text: Raw LLM text output

        Returns:
            Dict[str, FileMapping] mapping old paths to FileMapping objects

        Raises:
            ValueError: If parsing fails
        """
        pass


class ITextValidator(ABC):
    """
    Text validation and sanitization strategy interface (Application Strategy).

    Usage:
        validator = BasicTextValidator(max_length=150000)
        safe_text = validator.sanitize("raw text...")
        is_valid = validator.validate(safe_text)
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
    Template storage and loading interface (Outbound Port).

    This is an infrastructure port because it connects to external storage
    (filesystem, database, cloud storage, etc.).

    Usage:
        # Standalone usage
        loader = Jinja2TemplateLoader(base_path="prompts/")
        template = loader.load_template(provider="llama3b", version="v1", template_type="system")
        content = template.render(suggested_categories=["doc", "code"])

        # Composed with IPromptBuilder (application strategy)
        loader = Jinja2TemplateLoader(base_path="prompts/")
        builder = LlamaPromptBuilder(template_loader=loader, provider="llama3b", version="v1")
        messages = builder.build_prompt(text="...", instruction="...")
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
