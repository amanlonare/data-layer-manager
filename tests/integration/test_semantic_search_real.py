import math
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

import pytest
import torch

from data_layer_manager.application.ingestion.chunkers.fixed_chunker import (
    FixedSizeChunker,
)
from data_layer_manager.application.ingestion.parser_registry import ParserRegistry
from data_layer_manager.application.ingestion.service import IngestionService
from data_layer_manager.application.retrieval.service import HybridRetrievalService
from data_layer_manager.core.config import ChunkingSettings
from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.interfaces.retrieval import BaseFusion, BaseRetriever
from data_layer_manager.domain.interfaces.vector_store import BaseVectorStore
from data_layer_manager.domain.schemas.retrieval_filter import RetrievalFilter
from data_layer_manager.domain.schemas.scored_chunk import ScoredChunk
from data_layer_manager.infrastructure.embeddings.hf_engine import HFEmbeddingEngine
from data_layer_manager.infrastructure.parsers.text_parser import TextParser

# Patch torch.compiler for macOS/older torch versions where transformers expects it
# Moved inside a helper or here with noqa if needed, but we'll try top-level after imports
if not hasattr(torch, "compiler"):
    torch.compiler = MagicMock()


class RealInMemoryVectorStore(BaseVectorStore):
    """
    In-memory vector store that calculates real cosine similarity.
    """

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []

    def add_chunks(self, chunks: list[Chunk]) -> None:
        self.chunks.extend(chunks)

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = math.sqrt(sum(a * a for a in v1))
        magnitude2 = math.sqrt(sum(b * b for b in v2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def search(
        self,
        query_vector: list[float],
        limit: int = 4,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        # Filter chunks if metadata_filter is provided
        filtered_chunks = self.chunks
        if metadata_filter:
            filtered_chunks = [
                c
                for c in self.chunks
                if all(c.metadata.get(k) == v for k, v in metadata_filter.items())
            ]

        # Calculate similarities
        scored_chunks = [
            (self._cosine_similarity(query_vector, c.embedding or []), c)
            for c in filtered_chunks
            if c.embedding
        ]

        # Sort by similarity descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        return [c for _, c in scored_chunks[:limit]]

    def delete_document(self, document_id: UUID) -> None:
        self.chunks = [c for c in self.chunks if c.document_id != document_id]


class SimpleSemanticRetriever(BaseRetriever):
    """
    Wraps the RealInMemoryVectorStore as a BaseRetriever for testing HybridRetrievalService.
    """

    def __init__(
        self, engine: HFEmbeddingEngine, store: RealInMemoryVectorStore
    ) -> None:
        self.engine = engine
        self.store = store

    async def retrieve(
        self, query: str, filter_: RetrievalFilter, limit: int = 30
    ) -> list[ScoredChunk]:
        vector = self.engine.embed(query)
        # Convert filter to dict for the mock store
        metadata_filter = filter_.metadata.copy()
        if filter_.document_id:
            metadata_filter["document_id"] = filter_.document_id

        chunks = self.store.search(vector, limit=limit, metadata_filter=metadata_filter)

        # In a real scenario, we'd calculate real scores. Here we just return 1.0/rank
        return [
            ScoredChunk(chunk=c, score=1.0 / (i + 1), retriever_id="semantic")
            for i, c in enumerate(chunks)
        ]


class NoOpFusion(BaseFusion):
    """
    Simplest fusion for testing: returns the first set.
    """

    def fuse(
        self, results_sets: list[list[ScoredChunk]], limit: int = 20
    ) -> list[ScoredChunk]:
        if not results_sets:
            return []
        return results_sets[0][:limit]


@pytest.fixture
def real_e2e_setup() -> tuple[IngestionService, HybridRetrievalService]:
    # 1. Setup Ingestion Dependencies
    registry = ParserRegistry()
    registry.register(".txt", TextParser())
    test_settings = ChunkingSettings(default_size=200, default_overlap=0)
    chunker = FixedSizeChunker(settings=test_settings)
    repo = MagicMock()

    # 2. Setup REAL Vector Dependencies
    embedding_engine = HFEmbeddingEngine()
    vector_store = RealInMemoryVectorStore()

    # 3. Initialize Services
    ingestion_service = IngestionService(
        registry, chunker, repo, embedding_engine, vector_store
    )

    # 4. Initialize Modular Retrieval
    semantic_retriever = SimpleSemanticRetriever(embedding_engine, vector_store)
    retrieval_service = HybridRetrievalService(
        retrievers=[semantic_retriever], fusion_strategy=NoOpFusion()
    )

    return ingestion_service, retrieval_service


@pytest.mark.asyncio
async def test_real_hybrid_semantic_search(
    real_e2e_setup: tuple[IngestionService, HybridRetrievalService], tmp_path: Path
) -> None:
    """
    Verifies that real semantic search works using the new HybridRetrievalService orchestration.
    """
    ingestion_service, retrieval_service = real_e2e_setup

    # 1. Ingest distinct documents
    docs_to_ingest = {
        "space.txt": "Astronomy is the study of celestial objects and phenomena. Galaxies and stars are core topics.",
        "cooking.txt": "To bake a chocolate cake, you need flour, sugar, cocoa powder, and eggs in a mixing bowl.",
        "ai.txt": "Machine learning algorithms like transformers use self-attention mechanisms to process text data.",
    }

    for name, content in docs_to_ingest.items():
        p = tmp_path / name
        p.write_text(content)
        ingestion_service.ingest_file(
            str(p), source_metadata={"topic": name.split(".")[0]}
        )

    # 2. Test semantic relevance
    # Query about space should return the space chunk
    space_results = await retrieval_service.search(
        "Tell me about the stars and galaxies"
    )
    assert len(space_results) > 0
    assert "Astronomy" in space_results[0].chunk.content
    assert space_results[0].chunk.metadata["topic"] == "space"

    # Query about baking should return the cooking chunk
    cooking_results = await retrieval_service.search(
        "How do I make a dessert with cocoa?"
    )
    assert len(cooking_results) > 0
    assert "cake" in cooking_results[0].chunk.content
    assert cooking_results[0].chunk.metadata["topic"] == "cooking"
