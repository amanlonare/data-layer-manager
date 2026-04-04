from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from data_layer_manager.application.retrieval.service import HybridRetrievalService
from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.schemas.scored_chunk import ScoredChunk
from data_layer_manager.infrastructure.retrieval.fusion.rrf import RRFFusion


@pytest.fixture
def mock_chunk() -> Chunk:
    return Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="Test content",
        source_type="file",
        file_type="text",
    )


@pytest.mark.asyncio
async def test_hybrid_retrieval_orchestration(mock_chunk: Chunk) -> None:
    # 1. Setup mocks
    mock_retriever_1 = MagicMock()
    mock_retriever_1.retrieve = AsyncMock(
        return_value=[ScoredChunk(chunk=mock_chunk, score=0.9, rank=1)]
    )

    mock_retriever_2 = MagicMock()
    mock_retriever_2.retrieve = AsyncMock(
        return_value=[ScoredChunk(chunk=mock_chunk, score=0.8, rank=1)]
    )

    mock_fusion = MagicMock()
    mock_fusion.fuse = MagicMock(
        return_value=[ScoredChunk(chunk=mock_chunk, score=0.5, rank=1)]
    )

    service = HybridRetrievalService(
        retrievers=[mock_retriever_1, mock_retriever_2],
        fusion_strategy=mock_fusion,
    )

    # 2. Execute
    results = await service.search(query="test query")

    # 3. Verify
    assert len(results) == 1
    assert results[0].chunk.id == mock_chunk.id
    mock_retriever_1.retrieve.assert_called_once()
    mock_retriever_2.retrieve.assert_called_once()
    mock_fusion.fuse.assert_called_once()


def test_rrf_fusion_logic(mock_chunk: Chunk) -> None:
    # 1. Setup disparate results
    chunk_a = Chunk(
        id=uuid4(), document_id=uuid4(), content="A", source_type="f", file_type="t"
    )
    chunk_b = Chunk(
        id=uuid4(), document_id=uuid4(), content="B", source_type="f", file_type="t"
    )

    # Set 1: A is rank 1, B is rank 2
    results_1 = [
        ScoredChunk(chunk=chunk_a, score=1.0, rank=1),
        ScoredChunk(chunk=chunk_b, score=0.9, rank=2),
    ]

    # Set 2: B is rank 1, A is rank 2
    results_2 = [
        ScoredChunk(chunk=chunk_b, score=1.0, rank=1),
        ScoredChunk(chunk=chunk_a, score=0.9, rank=2),
    ]

    fusion = RRFFusion(k=60)

    # 2. Execute
    fused = fusion.fuse([results_1, results_2], limit=10)

    # 3. Verify
    # With equal rankings in reverse, scores should be near equal
    assert len(fused) == 2
    assert fused[0].score == fused[1].score
    assert {c.chunk.content for c in fused} == {"A", "B"}
