import json

from loguru import logger

from fileorg.cli.progress_display import ProgressDisplay
from fileorg.file_ops.adapters.parser_factory_adapter import ParserFactoryAdapter
from fileorg.file_ops.adapters.scanner import FileScanner
from fileorg.file_ops.application.parser_client import ParseFileClient
from fileorg.file_ops.ports.parser_ports import MultiParserOutput
from fileorg.file_ops.ports.scanner_ports import ReportOutput
from fileorg.llm_classifier.adapters.output_parsers.path_mapping_output_parser import PathMappingOutputParser
from fileorg.llm_classifier.adapters.output_parsers.summary_output_parser import SummaryOutputParser
from fileorg.llm_classifier.adapters.prompt_builders.classification_prompt_builder import ClassificationPromptBuilder
from fileorg.llm_classifier.adapters.prompt_builders.summary_prompt_builder import SummaryPromptBuilder
from fileorg.llm_classifier.adapters.sequential_file_id_mapper import SequentialFileIdMapper
from fileorg.llm_classifier.adapters.template_loader import Jinja2TemplateLoader
from fileorg.llm_classifier.application.file_classifier import FileClassifier
from fileorg.llm_classifier.infrastructure.factories.provider_factory import ProviderFactory
from fileorg.llm_classifier.ports.models import ClassificationOutput, LLMInput
from fileorg.organizer.adapters.local_executor import LocalFileOrganizer
from fileorg.organizer.application.organizer_use_case import FileOrganizerUseCase
from fileorg.organizer.ports import ExecutionResult


class FileCoordinator:
    """
    Main file coordinator orchestrating the complete 6-phase workflow.

    Phases:
        1. Scan: Discover files in the target directory
        2. Parse: Extract text content from files
        3. Classify: Use LLM to classify files into categories
        4. Backup: Create restoration point (integrated in Phase 5)
        5. Execute: Move files to organized locations
        6. Report: Generate organization report (TODO)
    """

    def __init__(self, args):
        """
        Initialize FileCoordinator with all dependencies.

        Args:
            args: Parsed command-line arguments containing:
                - command: "organize" or "restore"
                - path: Root directory for organization
                - preview: Dry-run mode flag
                - char_limit: Character limit for parsing
        """
        self.args = args
        self.progress = ProgressDisplay()

        # Components initialized on-demand based on user choice
        self.parser_factory = None
        self.parser_file_client = None
        self.classifier = None
        self.organizer_use_case = None

    def _init_parser(self):
        """Initialize file parser on-demand."""
        if self.parser_file_client is not None:
            return  # Already initialized

        logger.info("Initializing file parser...")
        self.parser_factory = ParserFactoryAdapter()
        self.parser_file_client = ParseFileClient(parser_factory=self.parser_factory, char_limit=self.args.char_limit)
        logger.success("File parser initialized")

    def _init_classifier(self):
        """Initialize LLM classifier with all dependencies."""
        try:
            logger.info("Initializing LLM classifier...")

            # 1. Auto-detect and create LLM provider
            self.llm_provider = ProviderFactory.create()
            logger.success(f"LLM Provider initialized: {self.llm_provider.__class__.__name__}")

            # 2. Initialize template loader
            # Templates are in fileorg/llm_classifier/prompts/
            self.template_loader = Jinja2TemplateLoader()
            logger.debug("Template loader initialized")

            # 3. Initialize prompt builders
            self.summary_builder = SummaryPromptBuilder(template_loader=self.template_loader, provider="llama3b", version="v1")
            self.classification_builder = ClassificationPromptBuilder(template_loader=self.template_loader, provider="llama3b", version="v1")
            logger.debug("Prompt builders initialized")

            # 4. Initialize output parsers
            self.summary_parser = SummaryOutputParser()
            self.path_mapping_parser = PathMappingOutputParser()
            logger.debug("Output parsers initialized")

            # 5. Initialize file ID mapper for stable file tracking
            # Fixes Issue #112: Double-space filename bug
            self.file_id_mapper = SequentialFileIdMapper(prefix="A", id_width=3)
            logger.debug("File ID mapper initialized (fixes double-space filename bug)")

            # 6. Initialize classifier with all dependencies
            self.classifier = FileClassifier(
                llm_provider=self.llm_provider,
                summary_prompt_builder=self.summary_builder,
                summary_parser=self.summary_parser,
                classification_prompt_builder=self.classification_builder,
                classification_parser=self.path_mapping_parser,
                file_id_mapper=self.file_id_mapper,
            )
            logger.success("FileClassifier initialized successfully with file ID mapping")

        except Exception as e:
            logger.error(f"Failed to initialize classifier: {e}")
            raise RuntimeError(f"Classifier initialization failed: {e}") from e

    def _init_organizer(self):
        """Initialize file organizer use case on-demand."""
        if self.organizer_use_case is not None:
            return  # Already initialized

        try:
            logger.info("Initializing file organizer...")
            local_organizer = LocalFileOrganizer()
            self.organizer_use_case = FileOrganizerUseCase(local_organizer)
            logger.success("FileOrganizerUseCase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize organizer: {e}")
            raise RuntimeError(f"Organizer initialization failed: {e}") from e

    def run(self):
        """Execute the appropriate command (organize or restore)."""
        if self.args.command == "organize":
            self.run_organize()
        elif self.args.command == "restore":
            self.run_restore()
        else:
            raise ValueError(f"Unknown command: {self.args.command}")

    def _prompt_existing_backup(self, backup_path):
        """
        Prompt user when existing backup is detected.

        Args:
            backup_path: Path to existing backup file

        Returns:
            str: User choice ("use_existing", "reorganize", "restore", "cancel")
        """
        logger.warning(f"Found existing backup at: {backup_path}")
        print("\n⚠️  Existing backup detected!")
        print(f"Location: {backup_path}")
        print("\nOptions:")
        print("  1. Use existing backup (fast, skip LLM)")
        print("  2. Re-organize (run full LLM classification again)")
        print("  3. Restore (undo previous organization)")
        print("  4. Cancel")

        choice = input("\nYour choice (1/2/3/4): ").strip()

        choice_map = {"1": "use_existing", "2": "reorganize", "3": "restore", "4": "cancel"}

        result = choice_map.get(choice)
        if result:
            logger.info(f"User chose: {result}")
        return result

    def _execute_from_backup(self, root_dir, preview):
        """
        Execute file organization using existing backup (no LLM inference).

        Args:
            root_dir: Root directory for organization
            preview: Whether this is a preview (dry-run)
        """
        from pathlib import Path

        logger.info("Executing organization from existing backup")
        print("✓ Using existing backup (skipping LLM classification)...\n")

        # Only need organizer for this operation
        self._init_organizer()

        try:
            # Load backup and reconstruct classification output
            backup_path = Path(root_dir) / ".backup" / "file_paths.json"
            classification_output = self._load_classification_from_backup(backup_path, root_dir)

            # Execute organization
            logger.info("=== Executing file organization from backup ===")
            self.progress.update("Moving files..." if not preview else "Generating preview...")

            exec_result = self.organizer_use_case.organize_files(classification_output=classification_output, root_dir=root_dir, dry_run=preview)

            logger.success(
                f"Execution complete: {exec_result.success_count} succeeded, "
                f"{exec_result.failed_count} failed, {exec_result.skipped_count} skipped "
                f"({exec_result.execution_time:.2f}s)"
            )

            if preview:
                logger.info("Preview mode: No files were actually moved")
            else:
                logger.info(f"Backup updated at: {exec_result.backup_dir}")

            # Print summary
            categories = {}  # Cannot determine categories from backup alone
            self._print_summary(exec_result, categories, preview)

            self.progress.done()
            logger.success("File organization completed successfully")

        except Exception as e:
            logger.error(f"Failed to execute from backup: {e}")
            self.progress.done()
            raise

    def _load_classification_from_backup(self, backup_path, root_dir):
        """
        Load classification output from existing backup file.

        Args:
            backup_path: Path to backup JSON file
            root_dir: Root directory for resolving relative paths

        Returns:
            ClassificationOutput reconstructed from backup
        """
        import json
        from pathlib import Path

        from fileorg.llm_classifier.ports.models import ClassificationOutput, FileMapping

        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            root_path = Path(root_dir).resolve()
            path_mappings = {}

            for record in backup_data.get("file_paths", []):
                initial_path = record.get("initial_path", "")
                new_path = record.get("new", "")

                # Resolve relative paths
                if Path(initial_path).is_absolute():
                    old_path_abs = initial_path
                else:
                    old_path_abs = str(root_path / initial_path)

                # Create FileMapping
                file_mapping = FileMapping(
                    old_path=old_path_abs,
                    new_relative_path=new_path,
                    category="From Backup",  # Category info not in backup
                    summary="",  # Summary not available in backup
                    reason="Loaded from existing backup",
                )

                path_mappings[old_path_abs] = file_mapping

            return ClassificationOutput(
                path_mappings=path_mappings,
                raw_responses={"stage1_summaries": "N/A (loaded from backup)", "stage2_classification": "N/A (loaded from backup)"},
            )

        except Exception as e:
            raise RuntimeError(f"Failed to load backup: {e}") from e

    def run_organize(self):
        """
        Execute the complete file organization workflow.

        Phases:
            1. Scan files in target directory
            2. Parse file contents
            3. Classify files using LLM
            4. Create backup (automatic in Phase 5)
            5. Execute file movements
            6. Generate report (TODO)
        """
        from pathlib import Path

        preview = self.args.preview
        root_dir = self.args.path

        logger.info(f"Starting file organization in {'preview' if preview else 'execution'} mode")
        logger.info(f"Target directory: {root_dir}")

        # Check if .backup already exists (before expensive initialization)
        backup_path = Path(root_dir) / ".backup" / "file_paths.json"
        if backup_path.exists():
            choice = self._prompt_existing_backup(backup_path)

            if choice == "use_existing":
                self._execute_from_backup(root_dir, preview)
                return
            elif choice == "restore":
                self.run_restore()
                return
            elif choice == "cancel":
                print("❌ Operation cancelled")
                return
            elif choice == "reorganize":
                logger.info("User chose to re-organize (overwrite existing backup)")
                print("✓ Proceeding with re-organization...\n")
                # Continue to full organization below
            else:
                print("❌ Invalid choice. Operation cancelled.")
                return

        # Initialize components only when needed
        self._init_parser()
        self._init_classifier()
        self._init_organizer()

        try:
            # === Phase 1: Scan ===
            logger.info("=== Phase 1: Scanning files ===")
            self.progress.update("Scanning files...")
            scanner = FileScanner(root_dir=root_dir)
            report_output: ReportOutput = scanner.generate_report()
            logger.success(f"Scan complete: {report_output.file_count} files found ({report_output.total_size} bytes)")

            # === Phase 2: Parse ===
            logger.info("=== Phase 2: Parsing file contents ===")
            self.progress.update("Parsing file contents...")
            multi_parser_output: MultiParserOutput = self.parser_file_client.parse_multiple(report_out=report_output)
            logger.success(f"Parse complete: {len(multi_parser_output)} files processed")
            logger.debug(f"Parsed files: {list(multi_parser_output.keys())[:5]}...")  # Show first 5

            # === Phase 3: Classify ===
            logger.info("=== Phase 3: Classifying files with LLM ===")
            self.progress.update("Classifying files with AI...")

            # Convert MultiParserOutput to LLMInput format
            # MultiParserOutput is Dict[str, str] where key=path, value=content
            llm_input_text = json.dumps(multi_parser_output, ensure_ascii=False)
            llm_input = LLMInput(text=llm_input_text, max_tokens=150000)

            # Execute two-stage classification
            classification_output: ClassificationOutput = self.classifier.classify(llm_input)
            logger.success(f"Classification complete: {len(classification_output.path_mappings)} files classified")

            # Log classification statistics
            categories = {}
            for file_mapping in classification_output.path_mappings.values():
                category = file_mapping.category
                categories[category] = categories.get(category, 0) + 1

            logger.info(f"Classification breakdown: {dict(categories)}")

            # === Phase 4: Backup (automatic in Phase 5) ===
            logger.info("=== Phase 4: Creating backup (integrated in Phase 5) ===")

            # === Phase 5: Execute Organization ===
            logger.info(f"=== Phase 5: {'Previewing' if preview else 'Executing'} file organization ===")
            if preview:
                self.progress.update("Generating preview...")
            else:
                self.progress.update("Moving files...")

            exec_result: ExecutionResult = self.organizer_use_case.organize_files(
                classification_output=classification_output, root_dir=root_dir, dry_run=preview
            )

            logger.success(
                f"Execution complete: {exec_result.success_count} succeeded, "
                f"{exec_result.failed_count} failed, {exec_result.skipped_count} skipped "
                f"({exec_result.execution_time:.2f}s)"
            )

            if preview:
                logger.info("Preview mode: No files were actually moved")
            else:
                logger.info(f"Backup created at: {exec_result.backup_dir}")

            # === Phase 6: Generate Report (TODO) ===
            logger.info("=== Phase 6: Generating report ===")
            self.progress.update("Generating report...")

            # TODO: Integrate report_generator module when available
            # report_output = self.report_generator.generate_report(
            #     classification_output=classification_output,
            #     execution_result=exec_result,
            #     target_dir=root_dir
            # )
            # logger.success("Report generated")

            # Temporary summary output
            self._print_summary(exec_result, categories, preview)

            self.progress.done()
            logger.success("File organization completed successfully")

        except Exception as e:
            logger.error(f"File organization failed: {e}")
            self.progress.done()
            raise

    def run_restore(self):
        """
        Execute file restoration from backup.

        Reads .backup/file_paths.json and restores all files to their
        original locations.
        """
        root_dir = self.args.path

        logger.info(f"Starting file restoration from: {root_dir}")
        self.progress.update(f"Loading backup from {root_dir}...")

        try:
            # Confirm restoration
            logger.warning("This will move all files back to their original locations")
            confirm = input(f"Are you sure you want to restore from {root_dir}? (y/N): ").strip().lower()

            if confirm != "y":
                logger.info("Restoration cancelled by user")
                print("❌ Restoration cancelled")
                return

            # Initialize organizer (only component needed for restore)
            self._init_organizer()

            # Execute restoration
            self.progress.update("Restoring files...")
            restore_result = self.organizer_use_case.restore_files(root_dir=root_dir)

            # Log results
            logger.success(
                f"Restoration complete: {restore_result['restored']} restored, "
                f"{restore_result['failed']} failed, {restore_result['skipped']} skipped "
                f"(Total: {restore_result['total']})"
            )

            if restore_result["errors"]:
                logger.warning(f"Encountered {len(restore_result['errors'])} errors:")
                for error in restore_result["errors"][:10]:  # Show first 10 errors
                    logger.error(f"  - {error}")

            print(f"✅ Restoration complete: {restore_result['restored']}/{restore_result['total']} files restored")
            self.progress.done()

        except FileNotFoundError as e:
            logger.error(f"Backup not found: {e}")
            print(f"❌ Error: {e}")
            self.progress.done()
            raise

        except Exception as e:
            logger.error(f"Restoration failed: {e}")
            print(f"❌ Restoration failed: {e}")
            self.progress.done()
            raise

    def _print_summary(self, exec_result: ExecutionResult, categories: dict, is_preview: bool):
        """
        Print a temporary summary of organization results.

        This will be replaced by the full report generator module in Phase 6.

        Args:
            exec_result: Execution result from organizer
            categories: Dictionary of category -> file count
            is_preview: Whether this was a preview (dry-run)
        """
        print("\n" + "=" * 60)
        if is_preview:
            print("📋 ORGANIZATION PREVIEW")
        else:
            print("✅ ORGANIZATION COMPLETE")
        print("=" * 60)

        print("\n📊 Summary:")
        print(f"  Total files:     {exec_result.total_count}")
        print(f"  Succeeded:       {exec_result.success_count} ✓")
        print(f"  Failed:          {exec_result.failed_count} ✗")
        print(f"  Skipped:         {exec_result.skipped_count} ⊘")
        print(f"  Execution time:  {exec_result.execution_time:.2f}s")

        print(f"\n📁 Categories ({len(categories)}):")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {category}: {count} files")

        if not is_preview:
            print(f"\n💾 Backup: {exec_result.backup_dir}")

        if exec_result.failed_count > 0:
            print("\n⚠️  Failed operations:")
            for op in exec_result.operations:
                if op.status == "failed":
                    print(f"  • {op.old_path}")
                    print(f"    → Error: {op.error}")

        print("\n" + "=" * 60 + "\n")
