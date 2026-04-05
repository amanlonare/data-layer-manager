from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from data_layer_manager.domain.entities.chunk import Chunk


class BaseGraphStore(ABC):
    """
    Interface for graph store operations.
    """

    @abstractmethod
    def upsert_document(self, document_id: UUID, metadata: dict[str, Any]) -> None:
        """
        Upserts a document node into the graph.
        """

    @abstractmethod
    def upsert_chunks(self, chunks: list[Chunk]) -> None:
        """
        Upserts chunk nodes and their relationships to the document into the graph.
        """

    @abstractmethod
    def delete_document(self, document_id: UUID) -> None:
        """
        Deletes a document and its associated chunks from the graph.
        """
