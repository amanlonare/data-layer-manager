from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from data_layer_manager.core.config import EmbeddingSettings
from data_layer_manager.infrastructure.embeddings.hf_engine import HFEmbeddingEngine


@pytest.fixture
def mock_st_model() -> Generator[MagicMock, None, None]:
    with patch(
        "data_layer_manager.infrastructure.embeddings.hf_engine.SentenceTransformer"
    ) as mock:
        model_instance = MagicMock()
        mock.return_value = model_instance
        # Mock dimension
        model_instance.get_sentence_embedding_dimension.return_value = 384
        # Mock encode to return a numpy array
        model_instance.encode.return_value = MagicMock(tolist=lambda: [0.1] * 384)
        yield model_instance


def test_hf_engine_initialization(mock_st_model: MagicMock) -> None:
    settings = EmbeddingSettings(model_name="test-model")
    engine = HFEmbeddingEngine(settings=settings)
    assert engine.dimension == 384


def test_hf_engine_embed(mock_st_model: MagicMock) -> None:
    settings = EmbeddingSettings(model_name="test-model")
    engine = HFEmbeddingEngine(settings=settings)
    vector = engine.embed("sample text")

    assert len(vector) == 384
    assert all(x == 0.1 for x in vector)
    mock_st_model.encode.assert_called_with("sample text")


def test_hf_engine_embed_batch(mock_st_model: MagicMock) -> None:
    # Adjust return value for batch
    mock_st_model.encode.return_value = MagicMock(
        tolist=lambda: [[0.1] * 384, [0.2] * 384]
    )

    settings = EmbeddingSettings(model_name="test-model")
    engine = HFEmbeddingEngine(settings=settings)
    vectors = engine.embed_batch(["text1", "text2"])

    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384
    assert vectors[1][0] == 0.2


@pytest.mark.asyncio
async def test_hf_engine_aembed(mock_st_model: MagicMock) -> None:
    settings = EmbeddingSettings(model_name="test-model")
    engine = HFEmbeddingEngine(settings=settings)
    vector = await engine.aembed("async text")

    assert len(vector) == 384
    mock_st_model.encode.assert_called_with("async text")
