from collections.abc import Generator
from datetime import datetime
from uuid import uuid4

import pytest
from qdrant_client import QdrantClient
from testcontainers.qdrant import QdrantContainer

from data_layer_manager.core.config import EmbeddingSettings, QdrantSettings, Settings
from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.infrastructure.vectorstores.qdrant.store import (
    QdrantVectorStore,
)


@pytest.fixture(scope="module")
def qdrant_container() -> Generator[QdrantContainer, None, None]:
    with QdrantContainer("qdrant/qdrant:latest") as qdrant:
        yield qdrant


@pytest.fixture
def qdrant_client(qdrant_container: QdrantContainer) -> QdrantClient:
    # Manually construct URL as get_connection_url might be missing/broken in some versions
    host = qdrant_container.get_container_host_ip()
    port = qdrant_container.get_exposed_port(6333)
    return QdrantClient(url=f"http://{host}:{port}")


@pytest.fixture
def mock_settings(qdrant_container: QdrantContainer) -> Settings:
    host = qdrant_container.get_container_host_ip()
    port = qdrant_container.get_exposed_port(6333)
    url = f"http://{host}:{port}"
    return Settings(
        qdrant=QdrantSettings(url=url, collection_name="test_collection"),
        embeddings=EmbeddingSettings(
            dimension=128  # Small dimension for testing
        ),
    )


def test_qdrant_store_lifecycle(
    qdrant_client: QdrantClient,
    mock_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Mock get_settings to return our test-specific settings
    import data_layer_manager.infrastructure.vectorstores.qdrant.store as store_mod

    monkeypatch.setattr(store_mod, "get_settings", lambda: mock_settings)

    store = QdrantVectorStore(client=qdrant_client)

    # 1. Verify collection creation
    assert qdrant_client.collection_exists("test_collection")

    # 2. Add Chunks for two documents (doc_a and doc_b)
    doc_a_id = uuid4()
    doc_b_id = uuid4()

    chunks_a = [
        Chunk(
            id=uuid4(),
            document_id=doc_a_id,
            content=f"Doc A content {i}",
            # Create a specific directional pattern for Doc A
            embedding=[0.1 if j == i else 0.01 for j in range(128)],
            source_type="file",
            source_category="research",
            file_type="pdf",
            metadata={"chunk_index": i, "source_locator": f"page_{i}"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        for i in range(2)
    ]

    chunks_b = [
        Chunk(
            id=uuid4(),
            document_id=doc_b_id,
            content=f"Doc B content {i}",
            # Create a completely different directional pattern for Doc B
            embedding=[0.5 if j == (i + 50) else 0.05 for j in range(128)],
            source_type="web",
            source_category="wiki",
            file_type="html",
            metadata={"chunk_index": i, "source_locator": f"url_{i}"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        for i in range(2)
    ]

    store.add_chunks(chunks_a + chunks_b)

    # 3. Verify Payload Round-trip (doc_a)
    query_vec_a = chunks_a[0].embedding
    assert query_vec_a is not None
    results_a = store.search(query_vector=query_vec_a, limit=1)
    assert len(results_a) == 1
    hit = results_a[0]
    assert hit.content == chunks_a[0].content
    assert hit.document_id == doc_a_id
    assert hit.source_category == "research"
    assert hit.file_type == "pdf"
    assert hit.metadata["chunk_index"] == 0
    assert hit.metadata["source_locator"] == "page_0"

    # 4. Delete Doc A and verify isolation
    store.delete_document(doc_a_id)

    # Doc A should be gone
    results_a_after = store.search(query_vector=query_vec_a, limit=10)
    # Filter for doc_a explicitly just in case of overlaps
    doc_a_hits = [r for r in results_a_after if r.document_id == doc_a_id]
    assert len(doc_a_hits) == 0

    # Doc B should still be there
    query_vec_b = chunks_b[0].embedding
    assert query_vec_b is not None
    results_b = store.search(query_vector=query_vec_b, limit=1)
    assert len(results_b) == 1
    assert results_b[0].document_id == doc_b_id
    assert results_b[0].content == chunks_b[0].content
    # Deep verify Doc B payload round-trip
    assert results_b[0].source_category == "wiki"
    assert results_b[0].metadata["chunk_index"] == 0
    assert results_b[0].metadata["source_locator"] == "url_0"
