from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data_layer_manager.infrastructure.persistence.models.base import Base

if TYPE_CHECKING:
    from data_layer_manager.infrastructure.persistence.models.document import DocDBModel


class ChunkDBModel(Base):
    """
    Database model for the Chunk entity.
    """

    __tablename__ = "chunks"
    __table_args__ = (
        Index("ix_chunks_search_vector", "search_vector", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE")
    )

    content: Mapped[str] = mapped_column(Text)

    # Embedding vector (Dynamic dimension length)
    embedding: Mapped[list[float] | None] = mapped_column(Vector, nullable=True)

    # Keyword Search Vector (FTS)
    search_vector: Mapped[Any | None] = mapped_column(TSVECTOR, nullable=True)

    # Explicit core metadata (Mirrored from Doc/Extracted)
    source_type: Mapped[str] = mapped_column(String(50))
    source_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="PENDING")

    # Flexible metadata
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default={})

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    document: Mapped[DocDBModel] = relationship("DocDBModel", back_populates="chunks")
