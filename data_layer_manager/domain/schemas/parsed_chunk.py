from typing import Any

from pydantic import BaseModel, Field


class ParsedChunk(BaseModel):
    """
    Intermediate representation of a chunk before persistence.
    Carries structure and bounds for full traceability.
    """

    text: str
    start_offset: int
    end_offset: int
    chunk_strategy: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
