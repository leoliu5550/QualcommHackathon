from loguru import logger

from fileorg.cli.progress_display import ProgressDisplay
from fileorg.file_ops.adapters.parser_factory_adapter import ParserFactoryAdapter
from fileorg.file_ops.adapters.scanner import FileScanner
from fileorg.file_ops.application.parser_client import ParseFileClient
from fileorg.file_ops.ports.parser_ports import MultiParserOutput
from fileorg.file_ops.ports.scanner_ports import ReportOutput


class FileOrganizer:
    def __init__(self, args):
        self.args = args
        self.progress = ProgressDisplay()
        self.parser_factory = ParserFactoryAdapter()
        factory = ParserFactoryAdapter()
        self.parser_file_client = ParseFileClient(parser_factory=factory, char_limit=args.char_limit)

    def run(self):
        if self.args.command == "organize":
            self.run_organize()
        elif self.args.command == "restore":
            self.run_restore()

    def run_organize(self):
        preview = self.args.preview
        root_dir = self.args.path
        # === Phase 1: Scan ===
        logger.debug("start scanning")
        self.progress.update("start scanning...")
        self.scanner = FileScanner(root_dir=root_dir)
        logger.debug("generating scanning report")
        self.progress.update("generating scanning report...")
        report_output: ReportOutput = self.scanner.generate_report()

        # === Phase 2: Parse ===
        logger.debug("start parse the files")
        self.progress.update("start parse the files...")
        multi_parser_output: MultiParserOutput = self.parser_file_client.parse_multiple(report_out=report_output)
        logger.debug(f"multi_parser_output is \n{multi_parser_output}")

        # === Phase 3: Classify ===
        logger.debug("classifying files")
        self.progress.update("Classifying files...")

        # === Phase 4: Create Restoration Point ===
        logger.debug("Creating restoration point...")
        self.progress.update("Creating restoration point...")

        # === Phase 5: Execute Organization (non-preview mode) ===
        if not preview:
            logger.debug("Moving files...")
            self.progress.update("Moving files...")
        else:
            pass
            # exec_result = ExecutionResult(success=False, preview=True)

        # === Phase 6: Generate Report ===
        logger.debug("Generating report...")
        self.progress.update("Generating report...")

        self.progress.done()

    def run_restore(self):
        manifest = self.args.manifest
        self.progress.update(f"載入還原點: {manifest}")
        # restoration = RestorationPoint(manifest_path=manifest)

        # 模擬確認
        confirm = input(f"是否確定還原 {manifest}? (y/N): ").strip().lower()
        if confirm != "y":
            print("❌ 已取消還原。")
            return

        self.progress.update("執行還原中...")
        print("✅ 還原完成。")
        self.progress.done()
