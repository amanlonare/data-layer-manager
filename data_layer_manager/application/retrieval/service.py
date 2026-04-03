from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.interfaces.embeddings import BaseEmbeddingEngine
from data_layer_manager.domain.interfaces.vector_store import BaseVectorStore


class VectorRetrievalService:
    """
    Application service that provides semantic retrieval capabilities.
    Fulfills the minimal semantic retrieval path for Phase 2 validation.
    """

    def __init__(
        self,
        embedding_engine: BaseEmbeddingEngine,
        vector_store: BaseVectorStore,
    ):
        self._embedding_engine = embedding_engine
        self._vector_store = vector_store

    def search_semantic(self, query: str, limit: int = 5) -> list[Chunk]:
        """
        Embeds the query and performs a vector-based search.

        Args:
            query: The natural language search query.
            limit: Maximum number of results to return.

        Returns:
            A list of Chunk entities that are semantically relevant.
        """
        # 1. Generate query embedding
        query_vector = self._embedding_engine.embed(query)

        # 2. Perform search in vector store
        return self._vector_store.search(query_vector=query_vector, limit=limit)
