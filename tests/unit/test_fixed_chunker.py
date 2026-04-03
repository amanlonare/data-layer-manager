import pytest

from data_layer_manager.application.ingestion.chunkers.fixed_chunker import (
    FixedSizeChunker,
)
from data_layer_manager.domain.schemas.parsed_document import ParsedDocument
from data_layer_manager.infrastructure.config import ChunkingSettings


def test_fixed_chunker_basic() -> None:
    settings = ChunkingSettings(default_size=100, default_overlap=10)
    chunker = FixedSizeChunker(settings=settings)
    text = "A" * 150
    doc = ParsedDocument(
        title="Test", raw_content=text, source_locator="test.txt", metadata={}
    )

    chunks = chunker.chunk(doc)

    assert len(chunks) == 2
    assert chunks[0].text == "A" * 100
    assert chunks[0].start_offset == 0
    assert chunks[0].end_offset == 100

    assert chunks[1].text == "A" * 60
    assert chunks[1].start_offset == 90
    assert chunks[1].end_offset == 150


def test_fixed_chunker_small_text() -> None:
    settings = ChunkingSettings(default_size=100, default_overlap=20)
    chunker = FixedSizeChunker(settings=settings)
    text = "Short text"
    doc = ParsedDocument(title="Test", raw_content=text, source_locator="test.txt")

    chunks = chunker.chunk(doc)
    assert len(chunks) == 1
    assert chunks[0].text == "Short text"


def test_fixed_chunker_empty_text() -> None:
    settings = ChunkingSettings(default_size=100, default_overlap=20)
    chunker = FixedSizeChunker(settings=settings)
    doc = ParsedDocument(title="Empty", raw_content="", source_locator="test.txt")

    chunks = chunker.chunk(doc)
    assert len(chunks) == 0


def test_fixed_chunker_large_overlap() -> None:
    # Error case: overlap >= chunk_size
    with pytest.raises(ValueError, match="overlap must be smaller than chunk_size"):
        settings = ChunkingSettings(default_size=50, default_overlap=50)
        FixedSizeChunker(settings=settings)
