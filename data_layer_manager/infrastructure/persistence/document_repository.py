import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.entities.document import Document
from data_layer_manager.infrastructure.persistence.models import (
    ChunkDBModel,
    DocDBModel,
)


class SQLAlchemyDocumentRepository:
    """
    SQLAlchemy implementation of the document persistence layer.
    Handles mapping between Domain Entities and Persistence Models.
    """

    def __init__(self, session: Session):
        self._session = session

    def create_document(self, document: Document) -> None:
        """
        Persists a new document and its initial chunks to the database.
        """
        db_doc = DocDBModel(
            id=document.id,
            title=document.title,
            source_type=document.source_type,
            source_category=document.source_category,
            file_type=document.file_type,
            status=document.status,
            metadata_=document.metadata,
        )
        self._session.add(db_doc)

        # Add chunks if present
        for chunk in document.chunks:
            self._add_chunk_model(chunk)

        self._session.flush()

    def get_document(self, document_id: uuid.UUID) -> Document | None:
        """
        Retrieves a document and its chunks by ID.
        """
        stmt = select(DocDBModel).where(DocDBModel.id == document_id)
        result = self._session.execute(stmt).scalar_one_or_none()

        if not result:
            return None

        return self._map_to_entity(result)

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """
        Adds multiple chunks to existing documents.
        """
        for chunk in chunks:
            self._add_chunk_model(chunk)
        self._session.flush()

    def delete_document(self, document_id: uuid.UUID) -> None:
        """
        Deletes a document and all its associated chunks (via CASCADE).
        """
        stmt = delete(DocDBModel).where(DocDBModel.id == document_id)
        self._session.execute(stmt)
        self._session.flush()

    def _add_chunk_model(self, chunk: Chunk) -> None:
        """Internal helper to convert and add a chunk model."""
        db_chunk = ChunkDBModel(
            id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            embedding=chunk.embedding,
            source_type=chunk.source_type,
            source_category=chunk.source_category,
            file_type=chunk.file_type,
            status=chunk.status,
            metadata_=chunk.metadata,
        )
        self._session.add(db_chunk)

    def _map_to_entity(self, db_doc: DocDBModel) -> Document:
        """Maps a database model back to a domain entity."""
        chunks = [
            Chunk(
                id=c.id,
                document_id=c.document_id,
                content=c.content,
                embedding=c.embedding,
                source_type=c.source_type,
                source_category=c.source_category,
                file_type=c.file_type,
                status=c.status,
                metadata=c.metadata_ or {},
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in db_doc.chunks
        ]

        return Document(
            id=db_doc.id,
            title=db_doc.title,
            source_type=db_doc.source_type,
            source_category=db_doc.source_category,
            file_type=db_doc.file_type,
            status=db_doc.status,
            metadata=db_doc.metadata_ or {},
            chunks=chunks,
            created_at=db_doc.created_at,
            updated_at=db_doc.updated_at,
        )
