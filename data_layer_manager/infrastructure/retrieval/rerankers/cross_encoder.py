from sentence_transformers import CrossEncoder

from data_layer_manager.core.config import get_settings
from data_layer_manager.domain.interfaces.retrieval import BaseReranker
from data_layer_manager.domain.schemas.scored_chunk import ScoredChunk


class CrossEncoderReranker(BaseReranker):
    """
    Second-stage reranker implementation using Cross-Encoder models.
    Refines candidates by re-scoring the relationship between the query and chunk.
    """

    def __init__(self, model_name: str | None = None):
        settings = get_settings().reranking
        model_name = model_name or settings.model_name
        self.model = CrossEncoder(model_name)

    async def rerank(
        self, query: str, chunks: list[ScoredChunk], limit: int = 10
    ) -> list[ScoredChunk]:
        """
        Calculates and returns a reranked list of candidates based on Cross-Encoder relevance.
        """
        if not chunks:
            return []

        # Pairs for the Cross-Encoder: (Query, Document Content)
        pairs = [(query, scored_chunk.chunk.content) for scored_chunk in chunks]

        # Batch inference
        scores = self.model.predict(pairs)

        # Map scores back to the ScoredChunk wrapper
        for scored_chunk, score in zip(chunks, scores):
            scored_chunk.score = float(score)

        # Sort based on new Cross-Encoder scores
        reranked = sorted(chunks, key=lambda x: x.score, reverse=True)

        # Update absolute rank and return limited results
        for rank, scored_chunk in enumerate(reranked[:limit], start=1):
            scored_chunk.rank = rank

        return reranked[:limit]
