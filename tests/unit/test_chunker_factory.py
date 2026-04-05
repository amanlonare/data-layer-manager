import pytest

from data_layer_manager.application.ingestion.chunkers.factory import get_chunker
from data_layer_manager.application.ingestion.chunkers.fixed_chunker import (
    FixedSizeChunker,
)
from data_layer_manager.core.config import ChunkingSettings, ChunkingStrategy


def test_get_chunker_fixed() -> None:
    settings = ChunkingSettings(strategy=ChunkingStrategy.FIXED)
    chunker = get_chunker(settings)
    assert isinstance(chunker, FixedSizeChunker)


def test_get_chunker_semantic_raises_not_implemented() -> None:
    settings = ChunkingSettings(strategy=ChunkingStrategy.SEMANTIC)
    with pytest.raises(NotImplementedError):
        get_chunker(settings)


def test_get_chunker_recursive_raises_not_implemented() -> None:
    settings = ChunkingSettings(strategy=ChunkingStrategy.RECURSIVE)
    with pytest.raises(NotImplementedError):
        get_chunker(settings)
