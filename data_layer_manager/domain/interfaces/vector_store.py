from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from data_layer_manager.domain.entities.chunk import Chunk


class BaseVectorStore(ABC):
    """
    Abstract interface defining the boundary for vector store persistence.
    Concrete implementations (pgvector, Qdrant) must fulfill this contract.
    """

    @abstractmethod
    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Adds or updates chunks in the vector store."""

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        limit: int = 4,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """Performs a semantic similarity search."""

    @abstractmethod
    def delete_document(self, document_id: UUID) -> None:
        """Removes all chunks associated with a document ID from the vector store."""
