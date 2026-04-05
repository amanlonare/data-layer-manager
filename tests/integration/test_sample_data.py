from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from data_layer_manager.application.ingestion.chunkers.fixed_chunker import (
    FixedSizeChunker,
)
from data_layer_manager.application.ingestion.parser_registry import ParserRegistry
from data_layer_manager.application.ingestion.service import IngestionService
from data_layer_manager.core.config import ChunkingSettings
from data_layer_manager.infrastructure.parsers.html_parser import HTMLParser
from data_layer_manager.infrastructure.parsers.markdown_parser import MarkdownParser
from data_layer_manager.infrastructure.parsers.text_parser import TextParser


# Simple In-Memory Repo for testing
class InMemoryDocumentRepository:
    def __init__(self) -> None:
        self.documents: dict[str, Any] = {}

    def save(self, document: Any) -> None:
        self.documents[str(document.id)] = document


@pytest.fixture
def sample_data_dir() -> Path:
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def parser_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(".md", MarkdownParser())
    registry.register(".txt", TextParser())
    registry.register(".html", HTMLParser())
    return registry


@pytest.fixture
def ingestion_service(parser_registry: ParserRegistry) -> IngestionService:
    settings = ChunkingSettings(default_size=200, default_overlap=20)
    chunker = FixedSizeChunker(settings=settings)
    doc_repo = InMemoryDocumentRepository()

    # Mock Embeddings
    mock_embeddings = MagicMock()
    mock_embeddings.dimension = 384
    mock_embeddings.embed_batch.side_effect = lambda texts: [[0.1] * 384 for _ in texts]

    # Mock Vector Store
    mock_vector_store = MagicMock()

    return IngestionService(
        parser_registry=parser_registry,
        chunker=chunker,
        document_repository=doc_repo,
        embedding_engine=mock_embeddings,
        vector_store=mock_vector_store,
    )


def test_ingest_sample_html(
    ingestion_service: IngestionService, sample_data_dir: Path
) -> None:
    file_path = sample_data_dir / "sample.html"
    assert file_path.exists()

    doc = ingestion_service.ingest_file(str(file_path), {"source_category": "samples"})

    assert doc.status == "COMPLETED"
    assert "Semantic Retrieval with Local Vectors" in doc.title
    assert len(doc.chunks) > 0
    assert doc.chunks[0].metadata["parser_name"] == "HTMLParser-v1"


def test_ingest_sample_markdown(
    ingestion_service: IngestionService, sample_data_dir: Path
) -> None:
    file_path = sample_data_dir / "sample.md"
    assert file_path.exists()

    doc = ingestion_service.ingest_file(str(file_path), {"source_category": "samples"})

    assert doc.status == "COMPLETED"
    assert "Project Guide: Data Layer Manager" in doc.title
    assert len(doc.chunks) > 0
    assert doc.chunks[0].metadata["parser_name"] == "MarkdownParser-v1"


def test_ingest_sample_text(
    ingestion_service: IngestionService, sample_data_dir: Path
) -> None:
    file_path = sample_data_dir / "sample.txt"
    assert file_path.exists()

    doc = ingestion_service.ingest_file(str(file_path), {"source_category": "samples"})

    assert doc.status == "COMPLETED"
    # Text parser extracts first line as title
    assert doc.title == "This is a plain text file for Testing the TextParser."
    assert len(doc.chunks) > 0
    assert doc.chunks[0].metadata["parser_name"] == "TextParser-v1"
