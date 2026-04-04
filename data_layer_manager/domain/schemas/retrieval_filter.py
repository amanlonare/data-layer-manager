from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RetrievalFilter(BaseModel):
    """
    Standardized filter contract for all retrieval strategies.
    Combines first-class column filtering with flexible JSONB metadata filtering.
    """

    # Explicit column-level filters (for indexing/performance)
    document_id: UUID | None = None
    file_type: str | None = None
    source_category: str | None = None

    # Flexible metadata-level filters (JSONB equality)
    metadata: dict[str, Any] = Field(default_factory=dict)
