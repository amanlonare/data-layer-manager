from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from data_layer_manager.core.config import Settings, VectorBackend
from data_layer_manager.domain.interfaces.vector_store import BaseVectorStore
from data_layer_manager.infrastructure.vectorstores.pgvector.store import PGVectorStore
from data_layer_manager.infrastructure.vectorstores.qdrant.store import (
    QdrantVectorStore,
)

if TYPE_CHECKING:
    from qdrant_client import QdrantClient


def get_vector_store(
    settings: Settings,
    db_session: Session | None = None,
    qdrant_client: QdrantClient | None = None,
) -> BaseVectorStore:
    """
    Factory function to create a VectorStore instance based on settings.
    """
    backend = settings.vector_store.backend

    if backend == VectorBackend.PGVECTOR:
        if db_session is None:
            raise ValueError("PGVECTOR backend requires a database session.")
        return PGVectorStore(session=db_session)

    if backend == VectorBackend.QDRANT:
        return QdrantVectorStore(client=qdrant_client)

    raise ValueError(f"Unsupported vector backend: {backend}")
