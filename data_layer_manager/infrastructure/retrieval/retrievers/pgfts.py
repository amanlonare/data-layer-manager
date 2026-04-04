from sqlalchemy import func, select
from sqlalchemy.orm import Session

from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.interfaces.retrieval import BaseRetriever
from data_layer_manager.domain.schemas.retrieval_filter import RetrievalFilter
from data_layer_manager.domain.schemas.scored_chunk import ScoredChunk
from data_layer_manager.infrastructure.persistence.models import ChunkDBModel


class PostgresFTSRetriever(BaseRetriever):
    """
    Keyword search strategy using PostgreSQL Full-Text Search.
    Uses the `search_vector` (TSVector) column created in Phase 3.
    """

    def __init__(self, session: Session):
        self._session = session
        self.id = "pg_fts_keyword"

    async def retrieve(
        self, query: str, filter_: RetrievalFilter, limit: int = 30
    ) -> list[ScoredChunk]:
        """
        Retrieves top K chunks using lexical match (FTS) + hybrid filtering.
        """
        if not query:
            return []

        # 1. Create the query (English config)
        # Using plainto_tsquery for simple natural language or to_tsquery for advanced.
        ts_query = func.plainto_tsquery("english", query)

        # 2. Build the ranking score
        rank = func.ts_rank(ChunkDBModel.search_vector, ts_query)

        # 3. Base Query
        stmt = (
            select(ChunkDBModel)
            .where(ChunkDBModel.search_vector.op("@@")(ts_query))
            .order_by(rank.desc())
            .limit(limit)
        )

        # 4. Apply Hybrid Filtering (Synced with VectorRetriever for consistent contract)
        if filter_.document_id:
            stmt = stmt.where(ChunkDBModel.document_id == filter_.document_id)
        if filter_.file_type:
            stmt = stmt.where(ChunkDBModel.file_type == filter_.file_type)
        if filter_.source_category:
            stmt = stmt.where(ChunkDBModel.source_category == filter_.source_category)

        # JSONB Metadata Equity
        if filter_.metadata:
            for key, value in filter_.metadata.items():
                stmt = stmt.where(ChunkDBModel.metadata_[key].astext == str(value))

        # 5. Execute
        results = self._session.execute(stmt).scalars().all()

        # 6. Map results
        scored_chunks = []
        for r in results:
            chunk = Chunk.model_validate(r)
            scored_chunks.append(
                ScoredChunk(
                    chunk=chunk,
                    score=0.0,  # Rank Fusion will handle relative ordering
                    retriever_id=self.id,
                )
            )

        return scored_chunks
