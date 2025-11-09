from pathlib import Path

from fileorg.file_ops.adapters.file_parser.csv_parser import CsvParser
from fileorg.file_ops.adapters.file_parser.html_parser import HtmlParser
from fileorg.file_ops.adapters.file_parser.mhtml_parser import MhtmlParser
from fileorg.file_ops.adapters.file_parser.pdf_parser import PdfParser
from fileorg.file_ops.adapters.file_parser.ppt_parser import PptParser
from fileorg.file_ops.adapters.file_parser.txt_parser import TxtParser
from fileorg.file_ops.adapters.file_parser.word_parser import WordParser
from fileorg.file_ops.adapters.parser_factory_adapter import ParserFactoryAdapter
from fileorg.file_ops.application.parser_client import ParseFileClient
from fileorg.file_ops.ports.parser_ports import ParserOutput


class TestParserClient:
    file_pat = [Path("tests/example_data/interview prepare/Small Changes in AI.pptx"), Path("tests/example_data/entertainment/Short Stories.pdf")]
    factory = ParserFactoryAdapter()
    parser_file_client = ParseFileClient(parser_factory=factory, char_limit=10)

    def test_parse(self):
        output = self.parser_file_client.parse(file_path=self.file_pat[0])
        assert isinstance(output, ParserOutput)
        assert output.success
        assert output.content[:5] == "Small"

    def test_parse_multiple(self):
        outputs = self.parser_file_client.parse_multiple(file_paths=self.file_pat)
        for result in outputs:
            assert isinstance(result, ParserOutput)
            assert result.success


class TestAdapterParser:
    html_file = Path("tests/example_data/entertainment/raw_text.html")
    mhtml_file = Path("tests/example_data/202510D/Learning statistics through story_ students get creative with numbers.mhtml")
    pdf_file = Path("tests/example_data/entertainment/Short Stories.pdf")
    word_file = Path("tests/example_data/202510D/HealthOrganizations.docx")
    ppt_file = Path("tests/example_data/interview prepare/Small Changes in AI.pptx")
    txt_file = Path("tests/example_data/entertainment/書僕.txt")
    csv_file = Path("tests/example_data/202510D/aqx_p_432.csv")

    def test_HtmlParser(self):
        html_parser = HtmlParser()
        output = html_parser.parse(file_path=self.html_file, char_limit=10)
        assert isinstance(output, ParserOutput)
        assert output.success
        assert output.content[:4] == "Snow"

    def test_MhmlParser(self):
        mhtml_parser = MhtmlParser()
        output = mhtml_parser.parse(file_path=self.mhtml_file, char_limit=10)

        assert isinstance(output, ParserOutput)
        assert output.success
        assert output.content[:4] == "Lear"

    def test_PdfParser(self):
        pdf_parser = PdfParser()
        output = pdf_parser.parse(file_path=self.pdf_file, char_limit=10)

        assert isinstance(output, ParserOutput)
        assert output.success
        assert output.content[:4] == "\n\n\nC"

    def test_WordParser(self):
        word_parser = WordParser()
        output = word_parser.parse(file_path=self.word_file, char_limit=10)

        assert isinstance(output, ParserOutput)
        assert output.success
        assert output.content[:4] == "As h"

    def test_PptParser(self):
        ppt_parser = PptParser()
        output = ppt_parser.parse(file_path=self.ppt_file, char_limit=10)
        assert isinstance(output, ParserOutput)
        assert output.success
        assert output.content[:4] == "Smal"

    def test_TxtParser(self):
        txt_parser = TxtParser()
        output = txt_parser.parse(file_path=self.txt_file, char_limit=10)

        assert isinstance(output, ParserOutput)
        assert output.success
        assert output.content[:4] == "書僕 T"

    def test_CsvParser(self):
        csv_parser = CsvParser()
        output = csv_parser.parse(file_path=self.csv_file, char_limit=10)

        assert isinstance(output, ParserOutput)
        assert output.success
        assert output.content[:4] == "site"
