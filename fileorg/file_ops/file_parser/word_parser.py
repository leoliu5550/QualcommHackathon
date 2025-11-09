# word_parser.py
from pathlib import Path

from fileorg.file_ops.ports import IParser, ParserOutput


class WordParser(IParser):
    """Parser for Word documents (.docx, .doc)."""

    def _truncate_content(self, content: str, char_limit: int) -> str:
        if len(content) > char_limit:
            return content[:char_limit]
        return content

    def parse(self, file_path: Path, char_limit: int) -> ParserOutput:
        file_path = Path(file_path)
        try:
            text = ""
            if file_path.suffix.lower() == ".docx":
                import docx

                doc = docx.Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs]
                text = "\n".join(paragraphs)
            elif file_path.suffix.lower() == ".doc":
                import mammoth

                with open(file_path, "rb") as f:
                    result = mammoth.extract_raw_text(f)
                    text = result.value
            else:
                return ParserOutput(success=False, content="", error="Unsupported file type for WordParser")

            truncated_text = self._truncate_content(text, char_limit)
            return ParserOutput(success=True, content=truncated_text, error="")

        except Exception as e:
            return ParserOutput(success=False, content="", error=str(e))
