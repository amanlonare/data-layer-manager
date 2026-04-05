import logging
from typing import Any, LiteralString
from uuid import UUID

from neo4j import Driver, GraphDatabase

from data_layer_manager.core.config import get_settings
from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.interfaces.graph_store import BaseGraphStore

logger = logging.getLogger(__name__)


class Neo4jGraphStore(BaseGraphStore):
    """
    Neo4j implementation of the GraphStore interface.
    """

    def __init__(self, driver: Driver | None = None):
        """
        Initializes the Neo4j driver.
        """
        settings = get_settings()
        if driver:
            self._driver = driver
        else:
            self._driver = GraphDatabase.driver(
                settings.neo4j.url,
                auth=(settings.neo4j.username, settings.neo4j.password),
            )
        self._ensure_constraints()

    def _ensure_constraints(self) -> None:
        """
        Ensures that unique constraints exist for Document and Chunk IDs.
        """
        constraints: list[LiteralString] = [
            "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
        ]
        with self._driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.error(f"Failed to create Neo4j constraint: {e}")

    def upsert_document(self, document_id: UUID, metadata: dict[str, Any]) -> None:
        """
        Upserts a Document node.
        """
        import json

        def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, Any]:
            sanitized = {}
            for k, v in meta.items():
                if isinstance(v, (dict, list)):
                    sanitized[k] = json.dumps(v)
                elif v is None:
                    continue
                else:
                    sanitized[k] = v
            return sanitized

        query: LiteralString = """
        MERGE (d:Document {id: $id})
        SET d += $metadata,
            d.updated_at = datetime()
        """
        parameters = {
            "id": str(document_id),
            "metadata": _sanitize_metadata(metadata),
        }
        with self._driver.session() as session:
            session.run(query, parameters)

    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        """
        Upserts Chunk nodes and links them to their parent Document.
        """
        if not chunks:
            return

        import json

        def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, Any]:
            sanitized = {}
            for k, v in meta.items():
                if isinstance(v, (dict, list)):
                    sanitized[k] = json.dumps(v)
                elif v is None:
                    continue  # Neo4j properties can't be null, just omit
                else:
                    sanitized[k] = v
            return sanitized

        # Optimization: Use UNWIND for batch upsert
        query: LiteralString = """
        UNWIND $chunk_data AS data
        MERGE (c:Chunk {id: data.id})
        SET c.content = data.content,
            c.chunk_strategy = data.chunk_strategy,
            c.file_type = data.file_type,
            c.updated_at = datetime()
        SET c += data.metadata

        WITH c, data
        MERGE (d:Document {id: data.document_id})
        MERGE (d)-[r:HAS_CHUNK]->(c)
        SET r.strategy = data.chunk_strategy
        """

        chunk_data = []
        for chunk in chunks:
            chunk_data.append(
                {
                    "id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "content": chunk.content,
                    "chunk_strategy": chunk.chunk_strategy,
                    "file_type": chunk.file_type,
                    "metadata": _sanitize_metadata(chunk.metadata),
                }
            )

        parameters = {"chunk_data": chunk_data}

        with self._driver.session() as session:
            session.run(query, parameters)

    def delete_document(self, document_id: UUID) -> None:
        """
        Deletes a Document and its associated Chunks.
        """
        query: LiteralString = """
        MATCH (d:Document {id: $id})
        OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
        DETACH DELETE d, c
        """
        parameters = {"id": str(document_id)}
        with self._driver.session() as session:
            session.run(query, parameters)

    def close(self) -> None:
        """
        Closes the driver connection.
        """
        self._driver.close()
