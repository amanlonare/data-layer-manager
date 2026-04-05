from abc import ABC, abstractmethod

from data_layer_manager.domain.schemas.retrieval_filter import RetrievalFilter
from data_layer_manager.domain.schemas.scored_chunk import ScoredChunk


class BaseRetriever(ABC):
    """
    Interface for primary search strategies (Vector, FTS, Graph).
    """

    @abstractmethod
    async def retrieve(
        self, query: str, filter_: RetrievalFilter, limit: int = 30
    ) -> list[ScoredChunk]:
        """
        Perform the initial search and return a ranked list of scored chunks.
        """
        pass


class BaseFusion(ABC):
    """
    Interface for merging multiple ranked result sets.
    """

    @abstractmethod
    def fuse(
        self, results_sets: list[list[ScoredChunk]], limit: int = 20
    ) -> list[ScoredChunk]:
        """
        Combine disparate ranking outputs into a single unified result set (e.g., RRF).
        """
        pass


class BaseReranker(ABC):
    """
    Interface for second-stage refinement strategies (Cross-Encoders).
    """

    @abstractmethod
    async def rerank(
        self, query: str, chunks: list[ScoredChunk], limit: int = 10
    ) -> list[ScoredChunk]:
        """
        Re-score a small set of top candidates using computationally expensive models.
        """
        pass
