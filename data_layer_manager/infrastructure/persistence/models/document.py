from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data_layer_manager.infrastructure.persistence.models.base import Base

if TYPE_CHECKING:
    from data_layer_manager.infrastructure.persistence.models.chunk import ChunkDBModel


class DocDBModel(Base):
    """
    Database model for the Document entity.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))

    # Explicit core metadata (Hybrid approach)
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
    chunks: Mapped[list[ChunkDBModel]] = relationship(
        "ChunkDBModel", back_populates="document", cascade="all, delete-orphan"
    )
