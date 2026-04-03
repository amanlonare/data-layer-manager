from pathlib import Path
from typing import Any

import markdown_it
from bs4 import BeautifulSoup

from data_layer_manager.domain.interfaces.parser import BaseParser
from data_layer_manager.domain.schemas.parsed_document import ParsedDocument


class MarkdownParser(BaseParser):
    """
    Parses Markdown files to extract the main text and structural elements like H1 for title.
    """

    def __init__(self) -> None:
        self.md = markdown_it.MarkdownIt()

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

        tokens = self.md.parse(content)
        title = None

        # Simple extraction of the first H1 as the title
        for i, token in enumerate(tokens):
            if token.type == "heading_open" and token.tag == "h1":
                # The next token is usually inline containing the text
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    title = tokens[i + 1].content
                    break

        # In a more advanced implementation we'd strip the markdown cleanly.
        # For now, we store raw markdown or use BS4 to strip HTML rendered.
        html_content = self.md.render(content)
        clean_text = BeautifulSoup(html_content, "html.parser").get_text(separator="\n")

        return ParsedDocument(
            raw_content=clean_text,
            title=title,
            source_locator=source_metadata.get("locator", "unknown"),
            metadata={
                "parser_name": "MarkdownParser-v1",
                "source_metadata": source_metadata,
            },
        )
