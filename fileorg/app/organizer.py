import json
from pathlib import Path

from loguru import logger

from fileorg.file_ops.adapters.parser_factory_adapter import ParserFactoryAdapter
from fileorg.file_ops.adapters.scanner import FileScanner
from fileorg.file_ops.application.parser_client import ParseFileClient
from fileorg.file_ops.ports.parser_ports import MultiParserOutput
from fileorg.file_ops.ports.scanner_ports import ReportOutput

# 1. Create a factory that knows how to build parsers for different file types


class FileOrganizer:
    def __init__(self, char_limit: int = 500):
        self.parser_factory = ParserFactoryAdapter()
        factory = ParserFactoryAdapter()
        self.parser_file_client = ParseFileClient(parser_factory=factory, char_limit=char_limit)

    def start_organize(self, root_dir: Path):
        logger.debug("start scanning")
        self.scanner = FileScanner(root_dir=root_dir)
        report_output: ReportOutput = self.scanner.generate_report()
        logger.debug("start parse the file")
        multi_parser_output: MultiParserOutput = self.parser_file_client.parse_multiple(report_out=report_output)
        logger.debug(f"multi_parser_output is \n{json.dumps(multi_parser_output)}")
