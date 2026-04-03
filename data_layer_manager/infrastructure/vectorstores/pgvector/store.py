from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.interfaces.vector_store import BaseVectorStore
from data_layer_manager.infrastructure.persistence.models import ChunkDBModel


class PGVectorStore(BaseVectorStore):
    """
    PostgreSQL implementation of the VectorStore interface using pgvector.
    """

    def __init__(self, session: Session):
        """
        Initializes the store with a SQLAlchemy session.
        """
        self._session = session

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """
        Adds or updates chunks in the vector store.
        """
        for chunk in chunks:
            # Check if chunk already exists to prevent duplicates if necessary,
            # but usually ingestion service handles document-level deletion first.
            db_chunk = ChunkDBModel(
                id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
                embedding=chunk.embedding,
                source_type=chunk.source_type,
                source_category=chunk.source_category,
                file_type=chunk.file_type,
                status=chunk.status,
                metadata_=chunk.metadata,
            )
            self._session.add(db_chunk)
        self._session.flush()

    def search(
        self,
        query_vector: list[float],
        limit: int = 4,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """
        Performs a semantic similarity search using cosine distance.
        """
        # Calculate cosine distance
        distance = ChunkDBModel.embedding.cosine_distance(query_vector)

        stmt = select(ChunkDBModel).order_by(distance).limit(limit)

        # Apply metadata filters if provided (Deferred to Phase 3 usually, but support basic dict)
        if metadata_filter:
            for key, value in metadata_filter.items():
                if hasattr(ChunkDBModel, key):
                    stmt = stmt.where(getattr(ChunkDBModel, key) == value)

        results = self._session.execute(stmt).scalars().all()

        return [
            Chunk(
                id=r.id,
                document_id=r.document_id,
                content=r.content,
                embedding=r.embedding,
                source_type=r.source_type,
                source_category=r.source_category,
                file_type=r.file_type,
                status=r.status,
                metadata=r.metadata_ or {},
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in results
        ]

    def delete_document(self, document_id: UUID) -> None:
        """
        Removes all chunks associated with a document ID.
        """
        stmt = delete(ChunkDBModel).where(ChunkDBModel.document_id == document_id)
        self._session.execute(stmt)
        self._session.flush()
