from pathlib import Path
from typing import Any

import trafilatura
from bs4 import BeautifulSoup

from data_layer_manager.domain.interfaces.parser import BaseParser
from data_layer_manager.domain.schemas.parsed_document import ParsedDocument


class HTMLParser(BaseParser):
    """
    Parses HTML content to extract main article text, dropping navigation and footers.
    Uses trafilatura for layout-aware extraction.
    """

    def parse(
        self, source: bytes | str | Path, source_metadata: dict[str, Any]
    ) -> ParsedDocument:
        content: bytes | str
        if isinstance(source, Path):
            content = source.read_bytes()
        elif isinstance(source, str):
            content = source.encode("utf-8")
        elif isinstance(source, bytes):
            content = source
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

        # extract info using trafilatura
        extracted = trafilatura.bare_extraction(content)

        if extracted:
            clean_text = getattr(extracted, "text", "") or ""
            title = getattr(extracted, "title", None)
        else:
            clean_text = ""
            title = None

        if not title:
            # Fallback for minor snippets or missing title: basic BS4
            soup = BeautifulSoup(content, "html.parser")
            title_tag = soup.find("h1") or soup.find("title")
            if title_tag:
                title = title_tag.get_text().strip()

            if not clean_text:
                clean_text = soup.get_text(separator="\n")

        return ParsedDocument(
            raw_content=clean_text,
            title=title,
            source_locator=source_metadata.get("locator", "unknown"),
            metadata={
                "parser_name": "HTMLParser-v1",
                "source_metadata": source_metadata,
            },
        )
