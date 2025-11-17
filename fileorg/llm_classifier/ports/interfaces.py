"""
LLM Classifier Interfaces - Port Definitions
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    import jinja2

    from .models import ClassificationOutput, FileSummary, LLMInput


class IClassifierUseCase(ABC):
    """
    Text classification use case.

    Usage:
        classifier = MyClassifier()
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
    - Template-based prompts (using ITemplateLoader)
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
        builder = ClassificationPromptBuilder(
            template_loader=loader,
            provider="llama3b",
            version="v1"
        )
        messages = builder.build_prompt(text="classify this", instruction="...")

    Current Implementations:
        - ClassificationPromptBuilder: Jinja2 templates for classification tasks
        - SummaryPromptBuilder: Jinja2 templates for file summarization tasks
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
        template = loader.load_template(provider="llama3b", version="v1", template_type="classification_system")
        content = template.render(suggested_categories=["doc", "code"])

        # Composed with IPromptBuilder
        loader = Jinja2TemplateLoader(base_path="prompts/")
        builder = ClassificationPromptBuilder(template_loader=loader, provider="llama3b", version="v1")
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


class IFileIdMapper(ABC):
    """
    File ID mapping interface for converting file paths to stable identifiers.

    This interface follows the Single Responsibility Principle (SRP) by focusing
    solely on ID generation and path mapping. It solves the double-space filename
    bug by providing stable IDs that aren't affected by LLM text normalization.

    Usage:
        # Create mapper and generate IDs for files
        mapper = SequentialFileIdMapper()
        file_paths = ["/path/file1.txt", "/path/file2.txt"]
        id_map = mapper.create_mappings(file_paths)
        # Result: {"A001": "/path/file1.txt", "A002": "/path/file2.txt"}

        # Convert to ID-based representation for LLM
        id_content_map = {file_id: content[path] for file_id, path in id_map.items()}

        # Later, retrieve original path from ID
        original_path = mapper.get_path("A001")  # "/path/file1.txt"

    Implementations:
        - SequentialFileIdMapper: Simple A001, A002... scheme (recommended)
        - UUIDFileIdMapper: UUID-based IDs (for distributed systems)
        - HashFileIdMapper: Content-hash based IDs (for deduplication)
    """

    @abstractmethod
    def create_mappings(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Create ID mappings for a list of file paths.

        Args:
            file_paths: List of absolute file paths to map

        Returns:
            Dictionary mapping file IDs to original paths
            Example: {"A001": "/path/file1.txt", "A002": "/path/file2.txt"}

        Raises:
            ValueError: If file_paths is empty or contains duplicates
        """
        pass

    @abstractmethod
    def get_path(self, file_id: str) -> Optional[str]:
        """
        Retrieve original file path for a given file ID.

        Args:
            file_id: The file identifier (e.g., "A001")

        Returns:
            Original file path if found, None otherwise
        """
        pass

    @abstractmethod
    def get_id(self, file_path: str) -> Optional[str]:
        """
        Retrieve file ID for a given file path.

        Args:
            file_path: The absolute file path

        Returns:
            File ID if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all_mappings(self) -> Dict[str, str]:
        """
        Get all current ID-to-path mappings.

        Returns:
            Dictionary of all current mappings {file_id: file_path}
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Clear all mappings and reset internal state.

        Useful for processing new batches of files in the same session.
        """
        pass
