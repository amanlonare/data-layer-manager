import logging
from typing import Any

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

logger = logging.getLogger(__name__)


class InMemoryDocumentRepository:
    def __init__(self) -> None:
        self.documents: dict[Any, Any] = {}

    def save(self, document: Any) -> None:
        self.documents[str(document.id)] = document


@pytest.fixture
def parser_registry_fixture() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(".md", MarkdownParser())
    registry.register(".txt", TextParser())
    registry.register(".html", HTMLParser())
    return registry


@pytest.fixture
def chunker_fixture() -> FixedSizeChunker:
    # Pass explicit settings for testing
    settings = ChunkingSettings(default_size=100, default_overlap=20)
    return FixedSizeChunker(settings=settings)


@pytest.fixture
def document_repository_fixture() -> InMemoryDocumentRepository:
    return InMemoryDocumentRepository()


@pytest.fixture
def mock_embedding_engine() -> Any:
    from unittest.mock import MagicMock

    engine = MagicMock()
    engine.dimension = 384
    engine.embed.return_value = [0.1] * 384
    engine.embed_batch.side_effect = lambda texts: [[0.1] * 384 for _ in texts]
    return engine


@pytest.fixture
def mock_vector_store() -> Any:
    from unittest.mock import MagicMock

    return MagicMock()


@pytest.fixture
def ingestion_service_fixture(
    parser_registry_fixture: ParserRegistry,
    chunker_fixture: FixedSizeChunker,
    document_repository_fixture: InMemoryDocumentRepository,
    mock_embedding_engine: Any,
    mock_vector_store: Any,
) -> IngestionService:
    return IngestionService(
        parser_registry_fixture,
        chunker_fixture,
        document_repository_fixture,
        mock_embedding_engine,
        mock_vector_store,
    )


def test_markdown_ingestion_traceability(
    ingestion_service_fixture: IngestionService,
    document_repository_fixture: InMemoryDocumentRepository,
    tmp_path: Any,
) -> None:
    # 1. Ingest a sample .md file with two headers
    sample_md = tmp_path / "test_doc.md"
    sample_md.write_text(
        "# Main Title\n\nSome introductory content.\n\n## Subheader\n\nMore detailed content here."
    )

    # Run ingestion
    doc = ingestion_service_fixture.ingest_file(
        str(sample_md), source_metadata={"source_category": "test_docs"}
    )

    # 2. Asserts the Document status is COMPLETED
    assert doc.status == "COMPLETED"
    assert doc.title == "Main Title"

    # Verify in DB
    saved_doc = document_repository_fixture.documents[str(doc.id)]
    assert saved_doc.status == "COMPLETED"
    assert len(saved_doc.chunks) > 0

    # 3. Asserts the resulting Chunk entities have correct metadata
    for i, chunk in enumerate(saved_doc.chunks):
        assert chunk.document_id == doc.id
        assert chunk.metadata["chunk_index"] == i
        assert chunk.metadata["parser_name"] == "MarkdownParser-v1"
        assert chunk.metadata["source_locator"] == str(sample_md.absolute())

        # 4. Verifies file_type and strategy correctly propagated
        assert chunk.file_type == ".md"
        assert chunk.source_category == "test_docs"
        assert chunk.chunk_strategy == "fixed"

        assert "start_offset" in chunk.metadata
        assert "end_offset" in chunk.metadata

    # The first chunk should cover roughly 100 characters
    assert saved_doc.chunks[0].metadata["end_offset"] <= 100


def test_html_ingestion_trafilatura(
    ingestion_service_fixture: IngestionService,
    document_repository_fixture: InMemoryDocumentRepository,
    tmp_path: Any,
) -> None:
    # 1. Ingest a sample .html file
    sample_html = tmp_path / "test_article.html"
    sample_html.write_text(
        "<html><head><title>Main Title</title></head><body><h1>Main Title</h1><p>Some introductory content that is long enough to be considered an article by trafilatura.</p></body></html>"
    )

    # Run ingestion
    doc = ingestion_service_fixture.ingest_file(
        str(sample_html), source_metadata={"source_category": "web_docs"}
    )

    # 2. Asserts
    assert doc.status == "COMPLETED"
    assert doc.title == "Main Title"

    saved_doc = document_repository_fixture.documents[str(doc.id)]
    assert len(saved_doc.chunks) > 0
    assert saved_doc.chunks[0].metadata["source_locator"] == str(sample_html.absolute())
    assert saved_doc.chunks[0].metadata["parser_name"] == "HTMLParser-v1"
    assert saved_doc.chunks[0].source_category == "web_docs"
