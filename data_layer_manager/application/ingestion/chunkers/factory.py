from data_layer_manager.application.ingestion.chunkers.fixed_chunker import (
    FixedSizeChunker,
)
from data_layer_manager.core.config import ChunkingSettings, ChunkingStrategy
from data_layer_manager.domain.interfaces.chunker import BaseChunker


def get_chunker(settings: ChunkingSettings) -> BaseChunker:
    """
    Factory function to retrieve the appropriate chunker implementation based on strategy.
    """
    if settings.strategy == ChunkingStrategy.FIXED:
        return FixedSizeChunker(settings)

    if settings.strategy == ChunkingStrategy.SEMANTIC:
        raise NotImplementedError("Semantic chunking strategy is not yet implemented.")

    if settings.strategy == ChunkingStrategy.RECURSIVE:
        raise NotImplementedError("Recursive chunking strategy is not yet implemented.")

    raise ValueError(f"Unknown chunking strategy: {settings.strategy}")
