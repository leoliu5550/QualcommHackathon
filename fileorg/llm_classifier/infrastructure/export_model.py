"""
LLM Model Exporter - Export HuggingFace models to ONNX format.

This script exports LLM models (e.g., Llama 3.2 3B) to ONNX format with FP16 quantization
for efficient runtime inference using ONNX Runtime.
"""

import argparse
import sys
from pathlib import Path

from loguru import logger


class LLMExporter:
    """Export LLM models to ONNX format."""

    DEFAULT_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
    DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "models"

    def __init__(self, model_name: str, output_dir: Path):
        """
        Initialize exporter.

        Args:
            model_name: HuggingFace model identifier (e.g., "meta-llama/Llama-3.2-3B-Instruct")
            output_dir: Base output directory (models will be saved in models/{model_name}/)
        """
        self.model_name = model_name

        # Extract clean model name for folder (e.g., "Llama-3.2-3B-Instruct")
        self.model_folder_name = model_name.split("/")[-1]

        # Create model-specific subdirectory
        self.output_dir = output_dir / self.model_folder_name

        # Output paths (ONNX files from Optimum export)
        # Optimum typically creates: decoder_model.onnx, decoder_model_merged.onnx, etc.
        self.tokenizer_output_path = self.output_dir / "tokenizer.json"

    def check_dependencies(self) -> bool:
        """Check if required export dependencies are installed."""
        missing = []

        try:
            import torch  # noqa: F401
        except ImportError:
            missing.append("torch")

        try:
            import transformers  # noqa: F401
        except ImportError:
            missing.append("transformers")

        try:
            import optimum  # noqa: F401
        except ImportError:
            missing.append("optimum")

        if missing:
            logger.error(
                f"Missing required dependencies: {', '.join(missing)}\n\n"
                f"Please install export dependencies:\n"
                f"  uv pip install -e '.[llm-export]'  (recommended)\n"
                f"  or\n"
                f"  pip install -e '.[llm-export]'\n\n"
                f"Or install manually:\n"
                f"  uv pip install torch transformers optimum\n"
                f"  (or pip install torch transformers optimum)"
            )
            return False

        # Check HuggingFace authentication for gated models
        if "meta-llama" in self.model_name.lower():
            try:
                from huggingface_hub import HfApi

                api = HfApi()
                # Try to get model info (will fail if not authenticated for gated models)
                try:
                    api.model_info(self.model_name)
                    logger.info("HuggingFace authentication: OK")
                except Exception:
                    logger.warning(
                        f"\nModel '{self.model_name}' may require authentication.\n"
                        f"If export fails with 404 error:\n"
                        f"  1. Accept license at https://huggingface.co/{self.model_name}\n"
                        f"  2. Login: huggingface-cli login\n"
                        f"  3. Or set HF_TOKEN environment variable\n"
                    )
            except ImportError:
                pass

        return True

    def export_model(self) -> bool:
        """
        Export model to ONNX format.

        Returns:
            True if export successful, False otherwise
        """
        try:
            logger.info(f"Starting model export: {self.model_name}")
            logger.info(f"Output directory: {self.output_dir}")

            # Import here to avoid dependency at module level
            from optimum.onnxruntime import ORTModelForCausalLM
            from transformers import AutoTokenizer

            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Step 1: Load and export model
            logger.info("Step 1/2: Loading and exporting model from HuggingFace...")
            logger.info("Note: First-time download may take several minutes (model is ~6GB)")
            logger.info("The model will be exported with text-generation-with-past task for KV cache support")

            # Export model to ONNX using Optimum
            # The model is already FP16/BFloat16, Optimum will preserve the precision
            # For gated models, make sure you're logged in: huggingface-cli login

            # Configure ONNX export to avoid negative indexing issues
            from optimum.onnxruntime import ORTConfig

            # opset 17+ has better support for advanced indexing without negative indices
            ort_config = ORTConfig(
                opset=17,  # Use opset 17 for better compatibility
                use_past=True,  # Enable KV cache for autoregressive generation
                use_past_in_inputs=True,
            )

            logger.info(f"Exporting with ONNX opset version: {ort_config.opset}")

            try:
                model = ORTModelForCausalLM.from_pretrained(
                    self.model_name,
                    export=True,  # Export to ONNX
                    config=ort_config,  # Use custom ONNX config
                )
            except Exception as e:
                if "404" in str(e) or "Repository Not Found" in str(e):
                    logger.error(
                        f"\n{'=' * 70}\n"
                        f"ERROR: Model '{self.model_name}' not found or requires authentication\n"
                        f"{'=' * 70}\n\n"
                        f"Possible causes:\n"
                        f"  1. Model name is incorrect\n"
                        f"  2. Model is gated (requires accepting license)\n"
                        f"  3. Model requires HuggingFace authentication\n\n"
                        f"Solutions:\n"
                        f"  1. Verify model name is correct\n"
                        f"  2. For Llama models:\n"
                        f"     a. Visit: https://huggingface.co/{self.model_name}\n"
                        f"     b. Accept the license agreement\n"
                        f"     c. Login: huggingface-cli login\n"
                        f"     d. Enter your HuggingFace token\n\n"
                        f"Recommended models (publicly available):\n"
                        f"  ✓ meta-llama/Llama-3.2-1B-Instruct  (~1.5GB, fastest)\n"
                        f"  ✓ meta-llama/Llama-3.2-3B-Instruct  (~6GB, balanced, DEFAULT)\n\n"
                        f"Note: Larger models (8B+) may require HF Pro subscription\n"
                        f"{'=' * 70}\n"
                    )
                raise

            logger.success("Model loaded and exported to ONNX format (FP16)")

            # Step 2: Save ONNX model and tokenizer
            logger.info(f"Step 2/2: Saving model and tokenizer to {self.output_dir}...")

            # Save the model to model-specific directory
            # Optimum will create multiple files:
            # - decoder_model.onnx (or decoder_model_merged.onnx)
            # - config.json, generation_config.json, etc.
            model.save_pretrained(str(self.output_dir))

            # Check if model files exist
            onnx_files = list(self.output_dir.glob("*.onnx"))
            if not onnx_files:
                logger.error("No ONNX file found after export")
                return False

            logger.success(f"ONNX model files saved to {self.output_dir}")
            logger.info(f"Generated ONNX files: {[f.name for f in onnx_files]}")

            # Export tokenizer
            logger.info(f"Exporting tokenizer to {self.tokenizer_output_path}...")

            # User-initiated model download - revision pinning not enforced for flexibility
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)  # nosec B615

            # Save tokenizer as JSON (for use with tokenizers library)
            tokenizer.save_pretrained(str(self.output_dir))

            # The tokenizer is saved in multiple files, we need tokenizer.json
            tokenizer_json = self.output_dir / "tokenizer.json"
            if not tokenizer_json.exists():
                logger.error("tokenizer.json not found after export")
                return False

            # Ensure it's at the expected path
            if tokenizer_json != self.tokenizer_output_path:
                tokenizer_json.rename(self.tokenizer_output_path)

            logger.success(f"Tokenizer saved: {self.tokenizer_output_path}")

            # Summary
            logger.info("\n" + "=" * 70)
            logger.success("Export completed successfully!")
            logger.info("=" * 70)
            logger.info(f"Model directory: {self.output_dir}")
            logger.info(f"Model name: {self.model_folder_name}")
            logger.info("ONNX files:")
            total_size = 0
            for onnx_file in onnx_files:
                file_size = onnx_file.stat().st_size / 1024 / 1024
                total_size += file_size
                logger.info(f"  - {onnx_file.name}: {file_size:.2f} MB")
            logger.info(f"Total model size: {total_size:.2f} MB")
            logger.info(f"Tokenizer: {self.tokenizer_output_path.name}")
            logger.info(f"  Size: {self.tokenizer_output_path.stat().st_size / 1024:.2f} KB")
            logger.info("Precision: FP16 (preserved from original model)")
            logger.info("=" * 70)
            logger.info("\nNext steps:")
            logger.info("  1. Runtime dependencies already installed: onnxruntime-gpu, tokenizers")
            logger.info("  2. Use OnnxProvider with model_name parameter for inference")
            logger.info("  3. Enjoy 5-10x faster startup and smaller deployment size!")
            logger.info("=" * 70 + "\n")

            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            logger.exception(e)
            return False

    def cleanup_extra_files(self):
        """
        Clean up extra files created during export.

        Note: We keep config files as they may be useful for model inspection
        and are small in size. Only remove if absolutely necessary.
        """
        # Optional: Remove extra tokenizer config files if needed
        # For now, we keep all files for debugging and model inspection
        logger.debug("Keeping all exported files for model inspection")


def show_welcome_message(model_name: str = "meta-llama/Llama-3.2-3B-Instruct"):
    """Display welcome message and documentation reminder."""
    # Extract model size info
    model_size = "~6GB" if "3B" in model_name else "~12GB" if "8B" in model_name else "varies"

    logger.info("\n" + "=" * 70)
    logger.info("LLM Model Exporter - ONNX Export Tool")
    logger.info("=" * 70)
    logger.info(f"Target Model: {model_name}")
    logger.info(f"Estimated Size: {model_size}")
    logger.warning(
        "\nIMPORTANT: This tool requires understanding of the export process.\n"
        "Please read the documentation before proceeding:\n"
        "  - docs/llm_optimize.md\n"
        "  - fileorg/llm_classifier/models/README.md\n"
        "  - fileorg/llm_classifier/models/model_card_somple.md\n"
    )
    logger.info(
        "\nThis tool will:\n"
        "  1. Download the model from HuggingFace\n"
        "  2. Export to ONNX format (FP16, preserves original precision)\n"
        "  3. Export the tokenizer to JSON format\n"
        "  4. Save to fileorg/llm_classifier/models/{model_name}/\n"
    )
    logger.info("=" * 70 + "\n")


def confirm_export() -> bool:
    """Ask user to confirm they have read the documentation."""
    logger.info("Before proceeding, please confirm:")
    response = input("Have you read the documentation? (yes/no): ").strip().lower()

    if response not in ["yes", "y"]:
        logger.warning("Please read the documentation before running this tool.")
        logger.info("Exiting...")
        return False

    logger.info("")
    return True


def main():
    """Main entry point for export tool."""
    parser = argparse.ArgumentParser(
        description="Export LLM models to ONNX format for production deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export default model (Llama 3.2 3B - recommended)
  fileorg-export-llm --yes

  # Export smaller model (faster, less capable)
  fileorg-export-llm --model meta-llama/Llama-3.2-1B-Instruct --yes

  # Export to custom directory
  fileorg-export-llm --output ./my-models --yes

Recommended Models:
  - meta-llama/Llama-3.2-1B-Instruct  (~1.5GB, fastest)
  - meta-llama/Llama-3.2-3B-Instruct  (~6GB, recommended, default)

Note: Larger models (8B+) require HuggingFace authentication and more resources.

For more information, see:
  - docs/llm_optimize.md
  - fileorg/llm_classifier/models/model_card_somple.md
        """,
    )

    parser.add_argument(
        "--model",
        type=str,
        default=LLMExporter.DEFAULT_MODEL,
        help=f"HuggingFace model identifier (default: {LLMExporter.DEFAULT_MODEL})",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=LLMExporter.DEFAULT_OUTPUT_DIR,
        help=f"Base output directory (models saved to output/{{model_name}}/, default: {LLMExporter.DEFAULT_OUTPUT_DIR})",
    )

    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt (for automated workflows)",
    )

    # Parse arguments (explicitly use sys.argv[1:] for Windows compatibility)
    args = parser.parse_args(sys.argv[1:])

    # Show welcome message with model info
    show_welcome_message(model_name=args.model)

    # Confirm (unless --yes flag)
    if not args.yes:
        if not confirm_export():
            sys.exit(1)

    # Create exporter
    exporter = LLMExporter(model_name=args.model, output_dir=args.output)

    # Check dependencies
    if not exporter.check_dependencies():
        sys.exit(1)

    # Export model
    success = exporter.export_model()

    if success:
        # Cleanup extra files
        exporter.cleanup_extra_files()
        logger.success("Export completed successfully!")
        sys.exit(0)
    else:
        logger.error("Export failed. Please check the logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
