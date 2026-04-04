from data_layer_manager.domain.interfaces.retrieval import BaseFusion
from data_layer_manager.domain.schemas.scored_chunk import ScoredChunk


class RRFFusion(BaseFusion):
    """
    Reciprocal Rank Fusion (RRF) implementation.
    Standardized algorithm for merging multiple ranked result sets without comparable scores.
    """

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self, results_sets: list[list[ScoredChunk]], limit: int = 20
    ) -> list[ScoredChunk]:
        """
        Calculates the Reciprocal Rank Fusion score for each chunk detected across the different result sets.
        """
        # Map to store accumulated RRF scores
        # We index by chunk ID to ensure chunk identity is preserved
        chunk_map: dict[str, ScoredChunk] = {}
        rrf_scores: dict[str, float] = {}

        for results in results_sets:
            for rank, scored_chunk in enumerate(results, start=1):
                chunk_id = str(scored_chunk.chunk.id)

                if chunk_id not in chunk_map:
                    chunk_map[chunk_id] = scored_chunk
                    rrf_scores[chunk_id] = 0.0

                # RRF Formula: 1 / (k + rank)
                rrf_scores[chunk_id] += 1.0 / (self.k + rank)

        # Sort by accumulated RRF score descending
        sorted_ids = sorted(
            rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True
        )

        fused_results = []
        for rank, chunk_id in enumerate(sorted_ids[:limit], start=1):
            scored_chunk = chunk_map[chunk_id]
            # Update with fused score and rank
            scored_chunk.score = rrf_scores[chunk_id]
            scored_chunk.rank = rank
            fused_results.append(scored_chunk)

        return fused_results
