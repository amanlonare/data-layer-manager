from pathlib import Path
from typing import Any

from data_layer_manager.domain.interfaces.parser import BaseParser
from data_layer_manager.domain.schemas.parsed_document import ParsedDocument


class TextParser(BaseParser):
    """
    Pass-through parser for plain text files.
    """

    def parse(
        self, source: bytes | str | Path, source_metadata: dict[str, Any]
    ) -> ParsedDocument:
        content = ""
        if isinstance(source, Path):
            content = source.read_text(encoding="utf-8")
        elif isinstance(source, bytes):
            content = source.decode("utf-8")
        elif isinstance(source, str):
            content = source

        # Try to infer title from the first line heuristically if needed
        lines = content.strip().split("\n")
        title = lines[0][:100].strip() if lines else None

        return ParsedDocument(
            raw_content=content,
            title=title,
            source_locator=source_metadata.get("locator", "unknown"),
            metadata={
                "parser_name": "TextParser-v1",
                "source_metadata": source_metadata,
            },
        )
