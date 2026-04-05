from collections.abc import Generator
from uuid import uuid4

import pytest
from testcontainers.neo4j import Neo4jContainer

from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.infrastructure.graphstores.neo4j import Neo4jGraphStore


@pytest.fixture(scope="module")
def neo4j_container() -> Generator[Neo4jContainer, None, None]:
    with Neo4jContainer("neo4j:5.12.0-community") as container:
        yield container


@pytest.fixture
def graph_store(
    neo4j_container: Neo4jContainer,
) -> Generator[Neo4jGraphStore, None, None]:
    url = neo4j_container.get_connection_url()
    # Testcontainers usually uses 'neo4j' as default user and 'password' as default password
    # unless specified otherwise in the container init.
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(url, auth=("neo4j", "password"))

    # Clear database before each test to ensure isolation
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    store = Neo4jGraphStore(driver=driver)
    yield store
    store.close()


def test_neo4j_upsert_and_relationships(graph_store: Neo4jGraphStore) -> None:
    # Setup
    doc_id = uuid4()
    metadata = {"source": "test_metadata", "importance": "high"}

    chunk1 = Chunk(
        document_id=doc_id,
        content="This is chunk 1 content.",
        chunk_strategy="fixed",
        source_type="file",
        file_type="txt",
        metadata={"page": 1},
    )
    chunk2 = Chunk(
        document_id=doc_id,
        content="This is chunk 2 content.",
        chunk_strategy="fixed",
        source_type="file",
        file_type="txt",
        metadata={"page": 2},
    )

    # 1. Upsert Document
    graph_store.upsert_document(doc_id, metadata)

    # 2. Upsert Chunks
    graph_store.upsert_chunks([chunk1, chunk2])

    # 3. Verify via Cypher
    with graph_store._driver.session() as session:
        # Check Document node
        result = session.run(
            "MATCH (d:Document {id: $id}) RETURN d", {"id": str(doc_id)}
        )
        record = result.single()
        assert record is not None
        doc_node = record[0]
        assert (
            doc_node["title"] is None
        )  # We didn't set a title in the simple metadata dict
        assert doc_node["source"] == "test_metadata"

        # Check Chunk nodes and relationships
        result = session.run(
            "MATCH (d:Document {id: $id})-[:HAS_CHUNK]->(c:Chunk) RETURN c, d",
            {"id": str(doc_id)},
        )
        records = list(result)
        assert len(records) == 2

        contents = [r["c"]["content"] for r in records]
        assert "This is chunk 1 content." in contents
        assert "This is chunk 2 content." in contents

        # Check strategy property on relationship
        result = session.run(
            "MATCH (d:Document {id: $id})-[r:HAS_CHUNK]->(c:Chunk) RETURN r.strategy as strategy",
            {"id": str(doc_id)},
        )
        strategies = [r["strategy"] for r in result]
        assert all(s == "fixed" for s in strategies)


def test_neo4j_delete_document(graph_store: Neo4jGraphStore) -> None:
    # Setup
    doc_id = uuid4()
    graph_store.upsert_document(doc_id, {"title": "Delete Me"})
    graph_store.upsert_chunks(
        [
            Chunk(
                document_id=doc_id,
                content="Delete too",
                chunk_strategy="fixed",
                source_type="file",
                file_type="txt",
            )
        ]
    )

    # Verify exists
    with graph_store._driver.session() as session:
        record = session.run(
            "MATCH (n {id: $id}) RETURN count(n)", {"id": str(doc_id)}
        ).single()
        assert record is not None
        count = record[0]
        assert count == 1

    # Delete
    graph_store.delete_document(doc_id)

    # Verify gone
    with graph_store._driver.session() as session:
        record = session.run(
            "MATCH (n {id: $id}) RETURN count(n)", {"id": str(doc_id)}
        ).single()
        assert record is not None
        count = record[0]
        assert count == 0

        # Verify orphaned chunks are gone too
        record = session.run("MATCH (c:Chunk) RETURN count(c)").single()
        assert record is not None
        chunk_count = record[0]
        assert chunk_count == 0
