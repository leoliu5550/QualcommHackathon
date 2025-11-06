"""
Ports Module - Hexagonal Architecture

This module defines all port interfaces (contracts) for the LLM Classifier system.
Ports represent the boundaries of the application and define how the core business
logic interacts with the outside world.

Architecture Overview:
    - Inbound Ports: Entry points for external actors (use cases)
    - Outbound Ports: Dependencies the application needs (repositories, services)

Following SOLID principles:
    - Interface Segregation: Small, focused interfaces
    - Dependency Inversion: Depend on abstractions, not concretions
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


# ============================================================================
# Domain Models (Value Objects and Entities)
# ============================================================================

@dataclass
class ClassificationRequest:
    """Value object representing a document classification request."""
    content: str
    max_length: int = 500


@dataclass
class ClassificationResult:
    """Value object representing classification output."""
    folder_name: str
    confidence: Optional[float] = None


@dataclass
class FolderMapping:
    """Value object for folder name to group name mapping."""
    original_folder: str
    grouped_folder: str


@dataclass
class FilePathMapping:
    """Value object for file path transformation."""
    original_path: str
    new_path: str


@dataclass
class ProcessingResult:
    """Aggregate result of file processing operation."""
    file_mappings: List[FilePathMapping]
    folder_mappings: List[FolderMapping]
    stats: Optional[Dict[str, Any]] = None


# ============================================================================
# Inbound Ports (Use Cases - Entry Points)
# ============================================================================

class IClassifyDocumentUseCase(ABC):
    """
    Inbound Port: Document classification use case.

    This port defines how external actors can request document classification.
    Implementations orchestrate the classification process using domain logic
    and outbound ports.

    SOLID Principles:
        - Single Responsibility: Only handles document classification
        - Open/Closed: Extensible via new implementations
    """

    @abstractmethod
    def classify(self, request: ClassificationRequest) -> ClassificationResult:
        """
        Classify a document and return appropriate folder name.

        Args:
            request: Classification request containing document content

        Returns:
            ClassificationResult with folder name and optional confidence
        """
        pass


class IRemapFoldersUseCase(ABC):
    """
    Inbound Port: Folder remapping use case.

    Groups similar folder names to reduce redundancy and improve organization.
    """

    @abstractmethod
    def remap(self, folder_names: List[str]) -> List[FolderMapping]:
        """
        Group similar folder names together.

        Args:
            folder_names: List of candidate folder names

        Returns:
            List of mappings from original to grouped folder names
        """
        pass


class IProcessFilesUseCase(ABC):
    """
    Inbound Port: Batch file processing use case.

    Orchestrates the complete file organization workflow including
    classification, remapping, and path generation.
    """

    @abstractmethod
    def process(
        self,
        summaries_data: Dict[str, Any],
        base_output_dir: str = "./"
    ) -> ProcessingResult:
        """
        Process multiple files and generate organized structure.

        Args:
            summaries_data: Dictionary containing file summaries
            base_output_dir: Base directory for organized output

        Returns:
            ProcessingResult containing all mappings and statistics
        """
        pass


# ============================================================================
# Outbound Ports (Dependencies - External Services)
# ============================================================================

class ILLMPort(ABC):
    """
    Outbound Port: Language Model inference interface.

    Abstracts the LLM implementation details, allowing different backends
    (Qualcomm NPU, local transformers, cloud APIs) to be used interchangeably.

    SOLID Principles:
        - Liskov Substitution: Any LLM adapter can be substituted
        - Dependency Inversion: Application depends on this abstraction
    """

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 200
    ) -> str:
        """
        Generate text response from LLM.

        Args:
            messages: List of message dictionaries (role, content)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        pass


class IPromptBuilderPort(ABC):
    """
    Outbound Port: Prompt construction interface.

    Responsible for building optimized prompts for LLM inference.
    Separates prompt engineering logic from business logic.
    """

    @abstractmethod
    def build_classification_prompt(
        self,
        content: str,
        max_length: int = 500
    ) -> List[Dict[str, str]]:
        """
        Build a prompt for document classification.

        Args:
            content: Document content to classify
            max_length: Maximum content length to include

        Returns:
            List of message dictionaries for LLM
        """
        pass

    @abstractmethod
    def build_remapping_prompt(
        self,
        folder_names: List[str]
    ) -> List[Dict[str, str]]:
        """
        Build a prompt for folder name grouping.

        Args:
            folder_names: List of folder names to group

        Returns:
            List of message dictionaries for LLM
        """
        pass


class IOutputValidatorPort(ABC):
    """
    Outbound Port: Output validation and sanitization interface.

    Ensures LLM outputs meet format requirements and are safe for file system use.
    """

    @abstractmethod
    def validate_json(self, text: str) -> tuple[bool, str]:
        """
        Validate and fix JSON output.

        Args:
            text: Raw text output from LLM

        Returns:
            Tuple of (is_valid, cleaned_text)
        """
        pass

    @abstractmethod
    def sanitize_folder_name(self, name: str) -> str:
        """
        Sanitize folder name for file system compatibility.

        Args:
            name: Raw folder name

        Returns:
            Sanitized folder name safe for file systems
        """
        pass


class IConfigPort(ABC):
    """
    Outbound Port: Configuration management interface.

    Provides access to application configuration without coupling
    to specific configuration storage mechanisms.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        pass

    @abstractmethod
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM-specific configuration as dictionary."""
        pass

    @abstractmethod
    def get_prompt_config(self) -> Dict[str, Any]:
        """Get prompt engineering configuration as dictionary."""
        pass


class IPersistencePort(ABC):
    """
    Outbound Port: Data persistence interface.

    Abstracts storage mechanisms for results and intermediate data.
    """

    @abstractmethod
    def save_result(
        self,
        result: ProcessingResult,
        output_file: str
    ) -> None:
        """
        Save processing results to storage.

        Args:
            result: Processing result to save
            output_file: Output file path
        """
        pass

    @abstractmethod
    def load_result(self, input_file: str) -> ProcessingResult:
        """
        Load processing results from storage.

        Args:
            input_file: Input file path

        Returns:
            Loaded processing result
        """
        pass


# ============================================================================
# Factory Ports (for creating adapters)
# ============================================================================

class ILLMFactoryPort(ABC):
    """
    Factory port for creating LLM adapters.

    Enables flexible instantiation of different LLM backends.
    """

    @abstractmethod
    def create_llm(
        self,
        backend: str,
        config: Dict[str, Any]
    ) -> ILLMPort:
        """
        Create an LLM adapter instance.

        Args:
            backend: Backend type identifier
            config: Backend-specific configuration

        Returns:
            LLM adapter instance
        """
        pass


class IPromptBuilderFactoryPort(ABC):
    """
    Factory port for creating prompt builder adapters.
    """

    @abstractmethod
    def create_builder(
        self,
        version: str,
        use_few_shot: bool,
        use_domain_detection: bool
    ) -> IPromptBuilderPort:
        """
        Create a prompt builder instance.

        Args:
            version: Prompt template version
            use_few_shot: Enable few-shot learning
            use_domain_detection: Enable domain detection

        Returns:
            Prompt builder adapter instance
        """
        pass
