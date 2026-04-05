from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

import pytest

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
from data_layer_manager.infrastructure.parsers.text_parser import TextParser


class InMemoryVectorStore(BaseVectorStore):
    def __init__(self) -> None:
        self.chunks: list[Chunk] = []

    def add_chunks(self, chunks: list[Chunk]) -> None:
        self.chunks.extend(chunks)

    def search(
        self,
        query_vector: list[float],
        limit: int = 4,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        # Very simple "mock" similarity (just return all for validation of flow)
        return self.chunks[:limit]

    def delete_document(self, document_id: UUID) -> None:
        self.chunks = [c for c in self.chunks if c.document_id != document_id]


class SimpleMockRetriever(BaseRetriever):
    """
    Wraps the InMemoryVectorStore as a BaseRetriever for testing HybridRetrievalService.
    """

    def __init__(self, engine: MagicMock, store: InMemoryVectorStore) -> None:
        self.engine = engine
        self.store = store

    async def retrieve(
        self, query: str, filter_: RetrievalFilter, limit: int = 30
    ) -> list[ScoredChunk]:
        vector = self.engine.embed(query)
        chunks = self.store.search(vector, limit=limit)
        return [ScoredChunk(chunk=c, score=1.0, retriever_id="mock") for c in chunks]


class IdentityFusion(BaseFusion):
    def fuse(
        self, results_sets: list[list[ScoredChunk]], limit: int = 20
    ) -> list[ScoredChunk]:
        if not results_sets:
            return []
        return results_sets[0][:limit]


@pytest.fixture
def e2e_setup() -> tuple[IngestionService, HybridRetrievalService]:
    # 1. Setup Ingestion Dependencies
    registry = ParserRegistry()
    registry.register(".txt", TextParser())
    # Use explicit settings for the test
    test_settings = ChunkingSettings(default_size=100, default_overlap=0)
    chunker = FixedSizeChunker(settings=test_settings)
    repo = MagicMock()  # Mock metadata repo

    # 2. Setup Vector Dependencies
    embedding_engine = MagicMock()
    embedding_engine.embed.return_value = [0.1] * 384
    embedding_engine.embed_batch.side_effect = lambda texts: [
        [0.1] * 384 for _ in texts
    ]

    vector_store = InMemoryVectorStore()

    # 3. Initialize Services
    ingestion_service = IngestionService(
        registry, chunker, repo, embedding_engine, vector_store
    )

    # 4. Initialize Modular Retrieval
    mock_retriever = SimpleMockRetriever(embedding_engine, vector_store)
    retrieval_service = HybridRetrievalService(
        retrievers=[mock_retriever], fusion_strategy=IdentityFusion()
    )

    return ingestion_service, retrieval_service


@pytest.mark.asyncio
async def test_end_to_end_hybrid_flow(
    e2e_setup: tuple[IngestionService, HybridRetrievalService], tmp_path: Path
) -> None:
    ingestion_service, retrieval_service = e2e_setup

    # 1. Ingest a document
    file_path = tmp_path / "test.txt"
    file_path.write_text(
        "This is an extremely specific piece of information about antigravity."
    )

    doc = ingestion_service.ingest_file(
        str(file_path), source_metadata={"category": "test"}
    )

    # Verify vectors were generated and stored
    assert len(doc.chunks) > 0
    assert doc.chunks[0].embedding is not None
    assert len(doc.chunks[0].embedding) == 384

    # 2. Perform Retrieval
    results = await retrieval_service.search("Tell me about antigravity")

    # 3. Verify Results
    assert len(results) > 0
    assert "antigravity" in results[0].chunk.content
    assert results[0].chunk.document_id == doc.id

    # Verify dimension 8 traceability
    assert "chunk_index" in results[0].chunk.metadata
    assert results[0].chunk.metadata["source_locator"] == str(file_path.absolute())
