from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from data_layer_manager.core.config import get_settings
from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.interfaces.vector_store import BaseVectorStore

logger = logging.getLogger(__name__)


class QdrantVectorStore(BaseVectorStore):
    """
    Qdrant implementation of the VectorStore interface.
    """

    def __init__(self, client: QdrantClient | None = None):
        """
        Initializes the Qdrant client. If no client is provided, one is created from settings.
        """
        settings = get_settings()
        self._client = client or QdrantClient(
            url=settings.qdrant.url,
            api_key=settings.qdrant.api_key,
            prefer_grpc=settings.qdrant.prefer_grpc,
            timeout=settings.qdrant.timeout,
        )
        self._collection_name = settings.qdrant.collection_name
        self._vector_size = settings.embeddings.dimension

        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        """
        Checks if the collection exists, creating it if necessary.
        """
        try:
            if not self._client.collection_exists(self._collection_name):
                logger.info(f"Creating Qdrant collection: {self._collection_name}")
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=models.VectorParams(
                        size=self._vector_size,
                        distance=models.Distance.COSINE,
                    ),
                )
        except UnexpectedResponse as e:
            logger.error(f"Failed to check or create Qdrant collection: {e}")
            raise

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """
        Adds or updates chunks in the Qdrant vector store.
        """
        points = []
        for chunk in chunks:
            if not chunk.embedding:
                logger.warning(f"Skipping chunk {chunk.id} - no embedding found.")
                continue

            # Map the Chunk attributes to point payload
            payload = {
                "document_id": str(chunk.document_id),
                "content": chunk.content,
                "source_type": chunk.source_type,
                "source_category": chunk.source_category,
                "file_type": chunk.file_type,
                "status": chunk.status,
                "metadata": chunk.metadata,
                "created_at": chunk.created_at.isoformat(),
                "updated_at": chunk.updated_at.isoformat(),
            }

            points.append(
                models.PointStruct(
                    id=str(chunk.id),
                    vector=chunk.embedding,
                    payload=payload,
                )
            )

        if points:
            self._client.upsert(
                collection_name=self._collection_name,
                points=points,
                wait=True,
            )

    def search(
        self,
        query_vector: list[float],
        limit: int = 4,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """
        Performs a semantic similarity search using cosine distance.
        """
        query_filter = None
        if metadata_filter:
            must_conditions: list[Any] = []
            for key, value in metadata_filter.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )
            query_filter = models.Filter(must=must_conditions)

        # Use modern query_points API (Discovery API)
        search_result = self._client.query_points(
            collection_name=self._collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=True,
        ).points

        chunks = []
        for hit in search_result:
            p = hit.payload
            if p is None:
                continue

            # Reconstruct datetime from ISO string
            created_at_str = p.get("created_at")
            updated_at_str = p.get("updated_at")
            created_at = (
                datetime.fromisoformat(created_at_str)
                if created_at_str
                else datetime.utcnow()
            )
            updated_at = (
                datetime.fromisoformat(updated_at_str)
                if updated_at_str
                else datetime.utcnow()
            )

            # Ensure hit.id is a string/UUID and vector is a flat list
            point_id = str(hit.id)
            vector: list[float] | None = None
            if (
                isinstance(hit.vector, list)
                and len(hit.vector) > 0
                and not isinstance(hit.vector[0], list)
            ):
                vector = hit.vector  # type: ignore

            chunks.append(
                Chunk(
                    id=UUID(point_id),
                    document_id=UUID(str(p["document_id"])),
                    content=str(p["content"]),
                    embedding=vector,
                    source_type=str(p["source_type"]),
                    source_category=p.get("source_category"),
                    file_type=str(p["file_type"]),
                    status=p.get("status", "COMPLETED"),
                    metadata=p.get("metadata", {}),
                    created_at=created_at,
                    updated_at=updated_at,
                )
            )

        return chunks

    def delete_document(self, document_id: UUID) -> None:
        """
        Removes all chunks associated with a document ID.
        """
        self._client.delete(
            collection_name=self._collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id)),
                        )
                    ]
                )
            ),
            wait=True,
        )
