from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models in the project.
    Uses modern SQLAlchemy 2.0 type-mapping.
    """

    type_annotation_map = {
        dict[str, Any]: JSONB,
        uuid.UUID: PG_UUID(as_uuid=True),
    }


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


class ChunkDBModel(Base):
    """
    Database model for the Chunk entity.
    """

    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE")
    )

    content: Mapped[str] = mapped_column(Text)

    # Embedding vector (Defaulting to OpenAI 1536, but can be adjusted via migrations if needed)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

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
