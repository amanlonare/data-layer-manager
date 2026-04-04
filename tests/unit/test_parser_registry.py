from pathlib import Path
from typing import Any

import pytest

from data_layer_manager.application.ingestion.parser_registry import ParserRegistry
from data_layer_manager.domain.interfaces.parser import BaseParser


class MockParser(BaseParser):
    def parse(self, source: bytes | str | Path, source_metadata: dict[str, Any]) -> Any:
        return None


def test_parser_registry_registration() -> None:
    registry = ParserRegistry()
    parser = MockParser()
    registry.register(".txt", parser)

    assert registry.get_parser(".txt") == parser
    assert registry.get_parser("TXT") == parser  # Case insensitive


def test_parser_registry_fallback() -> None:
    registry = ParserRegistry()
    fallback = MockParser()
    registry.set_fallback(fallback)

    # Should return fallback for unknown extension
    assert registry.get_parser(".unknown") == fallback


def test_parser_registry_no_parser_error() -> None:
    registry = ParserRegistry()
    with pytest.raises(ValueError, match="No parser registered"):
        registry.get_parser(".missing")


def test_parser_registry_extension_formatting() -> None:
    registry = ParserRegistry()
    parser = MockParser()

    # Register without dot
    registry.register("pdf", parser)
    assert registry.get_parser(".pdf") == parser
    assert registry.get_parser("pdf") == parser
