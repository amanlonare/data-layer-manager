from pathlib import Path

from data_layer_manager.infrastructure.parsers.markdown_parser import MarkdownParser
from data_layer_manager.infrastructure.parsers.text_parser import TextParser


def test_markdown_parser_with_headers(tmp_path: Path) -> None:
    parser = MarkdownParser()
    sample_md = tmp_path / "test.md"
    sample_md.write_text("# Title\n\nContent body.")

    parsed_doc = parser.parse(sample_md, source_metadata={"category": "test"})

    assert parsed_doc.title == "Title"
    assert "Content body" in parsed_doc.raw_content
    assert "parser_name" in parsed_doc.metadata
    assert parsed_doc.metadata["parser_name"] == "MarkdownParser-v1"
    assert parsed_doc.metadata["source_metadata"]["category"] == "test"


def test_markdown_parser_no_header(tmp_path: Path) -> None:
    parser = MarkdownParser()
    sample_md = tmp_path / "no_header.md"
    sample_md.write_text("Just plain text.")

    parsed_doc = parser.parse(sample_md, source_metadata={})

    assert parsed_doc.title is None
    assert parsed_doc.raw_content.strip() == "Just plain text."


def test_text_parser(tmp_path: Path) -> None:
    parser = TextParser()
    sample_txt = tmp_path / "test.txt"
    sample_txt.write_text("Plain text content.")

    parsed_doc = parser.parse(sample_txt, source_metadata={})

    assert parsed_doc.title == "Plain text content."
    assert parsed_doc.raw_content == "Plain text content."
