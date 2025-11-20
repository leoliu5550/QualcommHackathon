"""
LLM Model Exporter - Export HuggingFace models to ONNX format.

This script exports LLM models (e.g., Llama 3.2 3B) to ONNX format with INT8 quantization
for efficient runtime inference using ONNX Runtime. Supports FP16 and INT8 quantization.
"""

import argparse
import sys
from pathlib import Path

from loguru import logger


class LLMExporter:
    """Export LLM models to ONNX format."""

    DEFAULT_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
    DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "models"

    def __init__(
        self,
        model_name: str,
        output_dir: Path,
        quantize: bool = True,
        skip_validation: bool = False,
        validation_samples: int = 5,
    ):
        """
        Initialize exporter.

        Args:
            model_name: HuggingFace model identifier (e.g., "meta-llama/Llama-3.2-3B-Instruct")
            output_dir: Base output directory (models will be saved in models/{model_name}/)
            quantize: If True, quantize to INT8 (default); if False, keep FP16
            skip_validation: Skip automatic validation of quantized model
            validation_samples: Number of samples to use for validation (default: 5)
        """
        self.model_name = model_name
        self.quantize = quantize
        self.skip_validation = skip_validation
        self.validation_samples = validation_samples

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

            # Step 2.5: Quantization (if enabled)
            precision = "FP16"  # Default
            if self.quantize:
                logger.info("\n" + "=" * 70)

                # Create backup of FP16 model for validation
                fp16_backup_dir = None
                if not self.skip_validation:
                    import shutil

                    fp16_backup_dir = self.output_dir.parent / f"{self.model_folder_name}_fp16_backup"
                    logger.info(f"Creating FP16 backup for validation: {fp16_backup_dir}")
                    if fp16_backup_dir.exists():
                        shutil.rmtree(fp16_backup_dir)
                    shutil.copytree(self.output_dir, fp16_backup_dir)

                # Quantize to INT8
                quantize_success = self.quantize_model()

                if quantize_success:
                    precision = "INT8"

                    # Validate quantized model
                    if not self.skip_validation and fp16_backup_dir:
                        validation_passed = self.validate_quantized_model(fp16_backup_dir)

                        if not validation_passed:
                            logger.warning("Validation failed - reverting to FP16 model")
                            # Restore FP16 model
                            import shutil

                            shutil.rmtree(self.output_dir)
                            fp16_backup_dir.rename(self.output_dir)
                            precision = "FP16"
                        else:
                            # Clean up backup
                            import shutil

                            shutil.rmtree(fp16_backup_dir)
                    elif fp16_backup_dir:
                        # Clean up backup even if validation skipped
                        import shutil

                        shutil.rmtree(fp16_backup_dir)
                else:
                    logger.warning("Quantization failed - keeping FP16 model")
                    precision = "FP16"
                    if fp16_backup_dir:
                        import shutil

                        shutil.rmtree(fp16_backup_dir)

                logger.info("=" * 70 + "\n")

            # Update onnx_files list after potential quantization
            onnx_files = list(self.output_dir.glob("*.onnx"))

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
            logger.info(f"Total model size: {total_size:.2f} MB (~{total_size / 1024:.1f} GB)")
            logger.info(f"Tokenizer: {self.tokenizer_output_path.name}")
            logger.info(f"  Size: {self.tokenizer_output_path.stat().st_size / 1024:.2f} KB")
            logger.info(f"Precision: {precision}")
            if precision == "INT8":
                logger.info("  Quantization: Dynamic (weights only, per-channel)")
                logger.info("  Size reduction: ~50% compared to FP16")
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

    def quantize_model(self) -> bool:
        """
        Quantize exported ONNX model to INT8 using dynamic quantization.

        Returns:
            True if quantization successful, False otherwise
        """
        try:
            logger.info("Step 2.5/3: Quantizing model to INT8 (dynamic quantization)...")

            from optimum.onnxruntime import ORTQuantizer
            from optimum.onnxruntime.configuration import AutoQuantizationConfig

            # Create quantizer from exported model
            quantizer = ORTQuantizer.from_pretrained(str(self.output_dir))

            # Dynamic quantization configuration
            # - is_static=False: No calibration data needed
            # - per_channel=True: Better accuracy with slightly larger size
            dqconfig = AutoQuantizationConfig.arm64(is_static=False, per_channel=True)

            logger.info("Quantization config: Dynamic (weights only), per-channel")

            # Create temporary directory for quantized output
            temp_quantized_dir = self.output_dir.parent / f"{self.model_folder_name}_quantized_temp"
            temp_quantized_dir.mkdir(parents=True, exist_ok=True)

            # Quantize model
            quantizer.quantize(
                save_dir=str(temp_quantized_dir),
                quantization_config=dqconfig,
            )

            logger.info("Quantization complete, replacing FP16 model with INT8 version...")

            # Move quantized ONNX files back to original location
            for onnx_file in temp_quantized_dir.glob("*.onnx"):
                target_file = self.output_dir / onnx_file.name
                if target_file.exists():
                    target_file.unlink()  # Remove old FP16 version
                onnx_file.replace(target_file)

            # Clean up temporary directory
            import shutil

            shutil.rmtree(temp_quantized_dir)

            logger.success("Model quantized to INT8 successfully")
            return True

        except Exception as e:
            logger.error(f"Quantization failed: {e}")
            logger.exception(e)
            logger.warning("Keeping FP16 model instead")
            return False

    def validate_quantized_model(self, fp16_model_dir: Path) -> bool:
        """
        Validate INT8 model accuracy against FP16 baseline.

        Args:
            fp16_model_dir: Path to FP16 baseline model

        Returns:
            True if validation passed, False otherwise
        """
        try:
            logger.info(f"Step 2.75/3: Validating INT8 model ({self.validation_samples} samples)...")

            import numpy as np
            import onnxruntime as ort
            from tokenizers import Tokenizer

            # Test prompts for file classification
            test_prompts = [
                "Classify this file: 2023_report.pdf",
                "What category is this: vacation_photo.jpg",
                "Organize: meeting_notes.txt",
                "File type: budget_2024.xlsx",
                "Categorize: presentation.pptx",
                "Classify: backup_20230101.tar.gz",
                "What is: README.md",
                "Organize file: invoice_march.pdf",
                "Category for: family_video.mp4",
                "File classification: setup.exe",
            ][: self.validation_samples]

            # Load tokenizer
            tokenizer = Tokenizer.from_file(str(self.tokenizer_output_path))

            # Load FP16 model
            fp16_onnx_file = next(fp16_model_dir.glob("*.onnx"))
            fp16_session = ort.InferenceSession(str(fp16_onnx_file))

            # Load INT8 model
            int8_onnx_file = next(self.output_dir.glob("*.onnx"))
            int8_session = ort.InferenceSession(str(int8_onnx_file))

            # Collect errors
            mse_errors = []

            for prompt in test_prompts:
                # Tokenize
                encoding = tokenizer.encode(prompt)
                input_ids = np.array([encoding.ids], dtype=np.int64)

                # Run FP16 model
                fp16_outputs = fp16_session.run(None, {"input_ids": input_ids})
                fp16_logits = fp16_outputs[0]

                # Run INT8 model
                int8_outputs = int8_session.run(None, {"input_ids": input_ids})
                int8_logits = int8_outputs[0]

                # Calculate MSE
                mse = np.mean((fp16_logits - int8_logits) ** 2)
                mse_errors.append(mse)

            # Calculate average MSE
            avg_mse = np.mean(mse_errors)
            max_mse = np.max(mse_errors)

            logger.info("Validation results:")
            logger.info(f"  Average MSE: {avg_mse:.6f}")
            logger.info(f"  Max MSE: {max_mse:.6f}")

            # Threshold: MSE should be very small (< 0.01 is acceptable)
            THRESHOLD = 0.01
            passed = avg_mse < THRESHOLD

            if passed:
                logger.success(f"✓ Validation PASSED (MSE {avg_mse:.6f} < {THRESHOLD})")
            else:
                logger.error(f"✗ Validation FAILED (MSE {avg_mse:.6f} >= {THRESHOLD})")
                logger.warning("INT8 model may have significant accuracy degradation")

            return passed

        except Exception as e:
            logger.error(f"Validation failed: {e}")
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


def show_welcome_message(model_name: str = "meta-llama/Llama-3.2-3B-Instruct", quantize: bool = True):
    """Display welcome message and documentation reminder."""
    # Extract model size info
    fp16_size = "~6GB" if "3B" in model_name else "~15GB" if "8B" in model_name else "varies"
    int8_size = "~3GB" if "3B" in model_name else "~8GB" if "8B" in model_name else "varies"
    model_size = int8_size if quantize else fp16_size

    # Warning for large models
    large_model_warning = ""
    if "8B" in model_name or "70B" in model_name:
        large_model_warning = (
            "\n⚠️  WARNING: Large model detected (8B+ parameters)\n"
            "   - Export may take 30+ minutes\n"
            "   - Requires 32GB+ RAM\n"
            "   - Disk space: 15-30GB\n"
        )

    logger.info("\n" + "=" * 70)
    logger.info("LLM Model Exporter - ONNX Export Tool")
    logger.info("=" * 70)
    logger.info(f"Target Model: {model_name}")
    logger.info(f"Estimated Size: {model_size}")
    logger.info(f"Precision: {'INT8 (Dynamic Quantization)' if quantize else 'FP16'}")
    if large_model_warning:
        logger.warning(large_model_warning)
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
        f"  2. Export to ONNX format ({'INT8 quantized' if quantize else 'FP16'})\n"
        "  3. Export the tokenizer to JSON format\n"
        f"{'  4. Validate quantized model accuracy (can skip with --skip-validation)' if quantize else ''}\n"
        f"  {'5' if quantize else '4'}. Save to fileorg/llm_classifier/models/{{model_name}}/\n"
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
  # Export default model with INT8 quantization (recommended)
  fileorg-export-llm --yes

  # Export FP16 (preserve original precision)
  fileorg-export-llm --fp16 --yes

  # Export with quantization but skip validation (faster)
  fileorg-export-llm --skip-validation --yes

  # Export smaller model
  fileorg-export-llm --model meta-llama/Llama-3.2-1B-Instruct --yes

  # Export to custom directory
  fileorg-export-llm --output ./my-models --yes

Recommended Models:
  - meta-llama/Llama-3.2-1B-Instruct  (~1.5GB FP16 / ~0.8GB INT8)
  - meta-llama/Llama-3.2-3B-Instruct  (~6GB FP16 / ~3GB INT8, default)

Note: Larger models (8B+) require HuggingFace authentication and more resources.

Quantization:
  By default, models are exported with INT8 dynamic quantization (~50% size reduction).
  Use --fp16 to preserve original FP16 precision.
  Quantized models are automatically validated against FP16 baseline.

For more information, see:
  - docs/llm_optimize.md
  - fileorg/llm_classifier/models/README.md
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
        "--fp16",
        action="store_true",
        help="Preserve FP16 precision (skip INT8 quantization). Use if you need maximum accuracy.",
    )

    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip automatic validation of quantized model (faster export, but no accuracy guarantee)",
    )

    parser.add_argument(
        "--validation-samples",
        type=int,
        default=5,
        help="Number of samples to use for validation (default: 5, range: 1-10)",
    )

    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt (for automated workflows)",
    )

    # Parse arguments (explicitly use sys.argv[1:] for Windows compatibility)
    args = parser.parse_args(sys.argv[1:])

    # Determine quantization setting
    quantize = not args.fp16  # Quantize by default unless --fp16 is specified

    # Validate validation_samples range
    if args.validation_samples < 1 or args.validation_samples > 10:
        logger.error("--validation-samples must be between 1 and 10")
        sys.exit(1)

    # Show welcome message with model info
    show_welcome_message(model_name=args.model, quantize=quantize)

    # Confirm (unless --yes flag)
    if not args.yes:
        if not confirm_export():
            sys.exit(1)

    # Create exporter
    exporter = LLMExporter(
        model_name=args.model,
        output_dir=args.output,
        quantize=quantize,
        skip_validation=args.skip_validation,
        validation_samples=args.validation_samples,
    )

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
