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
from data_layer_manager.application.retrieval.service import VectorRetrievalService
from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.interfaces.vector_store import BaseVectorStore
from data_layer_manager.infrastructure.config import ChunkingSettings
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


@pytest.fixture
def e2e_setup() -> tuple[IngestionService, VectorRetrievalService]:
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
    retrieval_service = VectorRetrievalService(embedding_engine, vector_store)

    return ingestion_service, retrieval_service


def test_end_to_end_semantic_flow(
    e2e_setup: tuple[IngestionService, VectorRetrievalService], tmp_path: Path
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
    results = retrieval_service.search_semantic("Tell me about antigravity")

    # 3. Verify Results
    assert len(results) > 0
    assert "antigravity" in results[0].content
    assert results[0].document_id == doc.id

    # Verify dimension 8 traceability
    assert "chunk_index" in results[0].metadata
    assert results[0].metadata["source_locator"] == str(file_path.absolute())
