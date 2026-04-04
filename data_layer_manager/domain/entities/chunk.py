from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """
    Represents a granular segment of data (text, code, etc.) extracted from a Document.
    """

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    content: str
    embedding: list[float] | None = None

    # Metadata Strategy: Explicit core fields + flexible JSONB-style dict
    source_type: str
    source_category: str | None = None
    file_type: str
    status: str = "PENDING"

    # Flexible document-specific metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
