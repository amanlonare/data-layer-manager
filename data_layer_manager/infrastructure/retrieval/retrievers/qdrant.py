import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from qdrant_client import QdrantClient, models

from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.interfaces.retrieval import BaseRetriever
from data_layer_manager.domain.schemas.retrieval_filter import RetrievalFilter
from data_layer_manager.domain.schemas.scored_chunk import ScoredChunk

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

    from data_layer_manager.core.config import Settings
    from data_layer_manager.domain.interfaces.embeddings import BaseEmbeddingEngine

logger = logging.getLogger(__name__)


class QdrantRetriever(BaseRetriever):
    """
    Semantic search strategy using Qdrant.
    Supports hybrid filtering (explicit fields + payload metadata).
    """

    def __init__(
        self,
        client: QdrantClient,
        embedding_service: BaseEmbeddingEngine,
        settings: Settings,
    ):
        self._client = client
        self._embedding_service = embedding_service
        self._collection_name = settings.qdrant.collection_name
        self.id = "qdrant_semantic"

    async def retrieve(
        self, query: str, filter_: RetrievalFilter, limit: int = 30
    ) -> list[ScoredChunk]:
        """
        Retrieves top K chunks using Qdrant vector similarity + filtering.
        """
        # 1. Embed the query
        query_vector: list[float] = self._embedding_service.embed(query)

        # 2. Build Qdrant Filter
        must_conditions: list[Any] = []

        # Explicit Fields
        if filter_.document_id:
            must_conditions.append(
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=str(filter_.document_id)),
                )
            )
        if filter_.file_type:
            must_conditions.append(
                models.FieldCondition(
                    key="file_type",
                    match=models.MatchValue(value=filter_.file_type),
                )
            )
        if filter_.source_category:
            must_conditions.append(
                models.FieldCondition(
                    key="source_category",
                    match=models.MatchValue(value=filter_.source_category),
                )
            )

        # Metadata Filters (Nested in Qdrant payload)
        if filter_.metadata:
            for key, value in filter_.metadata.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=f"metadata.{key}",
                        match=models.MatchValue(value=value),
                    )
                )

        query_filter = models.Filter(must=must_conditions) if must_conditions else None

        # 3. Search (Modern Discovery API)
        search_result = self._client.query_points(
            collection_name=self._collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
            with_vectors=True,
        ).points

        # 4. Map to ScoredChunk
        scored_chunks = []
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

            chunk = Chunk(
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

            scored_chunks.append(
                ScoredChunk(
                    chunk=chunk,
                    score=hit.score,
                    retriever_id=self.id,
                )
            )

        return scored_chunks
