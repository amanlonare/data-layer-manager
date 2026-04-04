from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from data_layer_manager.domain.entities.chunk import Chunk


class Document(BaseModel):
    """
    The top-level container for a source entry in the knowledge layer.
    """

    id: UUID = Field(default_factory=uuid4)
    title: str

    # Explicit core metadata
    source_type: str
    source_category: str | None = None
    file_type: str
    status: str = "PENDING"

    # Flexible document-specific metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Relationships
    chunks: list[Chunk] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
