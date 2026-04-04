from sqlalchemy import select
from sqlalchemy.orm import Session

from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.interfaces.embeddings import BaseEmbeddingEngine
from data_layer_manager.domain.interfaces.retrieval import BaseRetriever
from data_layer_manager.domain.schemas.retrieval_filter import RetrievalFilter
from data_layer_manager.domain.schemas.scored_chunk import ScoredChunk
from data_layer_manager.infrastructure.persistence.models import ChunkDBModel


class PGVectorRetriever(BaseRetriever):
    """
    Semantic search strategy using PGVector.
    Supports hybrid filtering (explicit columns + JSONB).
    """

    def __init__(self, session: Session, embedding_service: BaseEmbeddingEngine):
        self._session = session
        self._embedding_service = embedding_service
        self.id = "pgvector_semantic"

    async def retrieve(
        self, query: str, filter_: RetrievalFilter, limit: int = 30
    ) -> list[ScoredChunk]:
        """
        Retrieves top K chunks using vector similarity + hybrid filtering.
        """
        # 1. Embed the query
        query_vector = self._embedding_service.embed(query)

        # 2. Build similarity distance
        distance = ChunkDBModel.embedding.cosine_distance(query_vector)

        # 3. Build Query
        stmt = select(ChunkDBModel).order_by(distance).limit(limit)

        # 4. Apply Hybrid Filtering
        # Explicit Column Filters
        if filter_.document_id:
            stmt = stmt.where(ChunkDBModel.document_id == filter_.document_id)
        if filter_.file_type:
            stmt = stmt.where(ChunkDBModel.file_type == filter_.file_type)
        if filter_.source_category:
            stmt = stmt.where(ChunkDBModel.source_category == filter_.source_category)

        # JSONB Metadata Equality Filters
        if filter_.metadata:
            for key, value in filter_.metadata.items():
                # SQL: metadata ->> 'key' = 'value'
                stmt = stmt.where(ChunkDBModel.metadata_[key].astext == str(value))

        # 5. Execute
        results = self._session.execute(stmt).scalars().all()

        # 6. Map to ScoredChunk for traceability
        scored_chunks = []
        for r in results:
            # Reconstruct Chunk entity
            chunk = Chunk.model_validate(r)

            # Since distance calculation in SQL is not returned as a column easily here
            # (unless we select it explicitly), we'll use a placeholder or select it.
            # For modularity, we'll re-select the distance as a label if needed.

            scored_chunks.append(
                ScoredChunk(
                    chunk=chunk,
                    score=0.0,  # Rank Fusion only needs the relative order for now
                    retriever_id=self.id,
                )
            )

        return scored_chunks
