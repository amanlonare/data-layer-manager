import asyncio

from data_layer_manager.domain.interfaces.retrieval import (
    BaseFusion,
    BaseReranker,
    BaseRetriever,
)
from data_layer_manager.domain.schemas.retrieval_filter import RetrievalFilter
from data_layer_manager.domain.schemas.scored_chunk import ScoredChunk


class HybridRetrievalService:
    """
    Orchestrator for the modular retrieval pipeline.
    Combines disparate search strategies (semantic, lexical) into a unified result set.
    """

    def __init__(
        self,
        retrievers: list[BaseRetriever],
        fusion_strategy: BaseFusion,
        reranker: BaseReranker | None = None,
    ):
        self._retrievers = retrievers
        self._fusion_strategy = fusion_strategy
        self._reranker = reranker

    async def search(
        self,
        query: str,
        filter_: RetrievalFilter | None = None,
        limit: int = 10,
        rerank_threshold: int = 20,
    ) -> list[ScoredChunk]:
        """
        Executes the hybrid search pipeline:
        1. Parallel Retrieval (Async)
        2. Rank Fusion (RRF)
        3. Optional Reranking (Cross-Encoder)
        """
        if not filter_:
            filter_ = RetrievalFilter()

        # 1. Component Level Retrieval (Async Parallelism)
        # We retrieve more than the final limit to allow for fusion and reranking depth
        retrieval_tasks = [
            retriever.retrieve(query, filter_, limit=limit * 3)
            for retriever in self._retrievers
        ]

        # Parallel execution to minimize database round-trip latency
        # return_exceptions=True ensures one failing retriever doesn't crash the whole search
        responses = await asyncio.gather(*retrieval_tasks, return_exceptions=True)

        results_sets: list[list[ScoredChunk]] = []
        for i, resp in enumerate(responses):
            if isinstance(resp, (Exception, BaseException)):
                # Log the error but don't fail the entire request
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Retriever {self._retrievers[i].id} failed: {resp}")
                continue
            # Double check type narrowing
            if isinstance(resp, list):
                results_sets.append(resp)

        # 2. Rank Fusion (Reciprocal Rank Fusion)
        # Normalizes different scoring mechanisms into a single rank
        fused_results = self._fusion_strategy.fuse(results_sets, limit=rerank_threshold)

        # 3. Optional Second-Stage Reranking
        # Applied only to a bounded set of top candidates for performance
        if self._reranker and fused_results:
            final_results = await self._reranker.rerank(
                query, fused_results, limit=limit
            )
            return final_results

        # Return fused results capped at the requested limit if no reranker is active
        return fused_results[:limit]
