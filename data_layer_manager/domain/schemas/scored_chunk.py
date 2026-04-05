from pydantic import BaseModel

from data_layer_manager.domain.entities.chunk import Chunk


class ScoredChunk(BaseModel):
    """
    Traceable retrieval result wrapper.
    Preserves the original Chunk entity while adding pipeline-specific scoring and ranking.
    """

    chunk: Chunk
    score: float
    rank: int | None = None
    retriever_id: str | None = None  # Tracking which strategy found this result
