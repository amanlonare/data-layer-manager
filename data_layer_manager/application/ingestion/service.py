from pathlib import Path
from typing import Any

from data_layer_manager.application.ingestion.parser_registry import ParserRegistry
from data_layer_manager.core.config import ChunkingSettings, get_settings
from data_layer_manager.domain.entities.chunk import Chunk
from data_layer_manager.domain.entities.document import Document
from data_layer_manager.domain.interfaces.chunker import BaseChunker
from data_layer_manager.domain.interfaces.embeddings import BaseEmbeddingEngine
from data_layer_manager.domain.interfaces.vector_store import BaseVectorStore


class IngestionService:
    """
    Orchestrates the ingestion of a file: Parsing -> Chunking -> Metadata Enrichment -> Repository.
    """

    def __init__(
        self,
        parser_registry: ParserRegistry,
        chunker: BaseChunker,
        document_repository: Any,
        embedding_engine: BaseEmbeddingEngine,
        vector_store: BaseVectorStore,
        settings: ChunkingSettings | None = None,
    ):
        self.parser_registry = parser_registry
        self.chunker = chunker
        self.document_repository = document_repository
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.settings = settings or get_settings().chunking

    def ingest_file(self, file_path: str, source_metadata: dict[str, Any]) -> Document:
        """
        Main ingestion flow for a file.
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        # 1. Detect extension -> Get Parser -> parse()
        parser = self.parser_registry.get_parser(extension)

        source_metadata_enriched = source_metadata.copy()
        source_metadata_enriched["locator"] = str(path.absolute())

        parsed_doc = parser.parse(source=path, source_metadata=source_metadata_enriched)

        # 2. Produce Document entity with status IN_PROGRESS
        file_type = extension if extension else "unknown"
        source_category = source_metadata.get("source_category", "default")

        document = Document(
            title=parsed_doc.title or path.stem,
            source_type="file",
            source_category=source_category,
            file_type=file_type,
            status="IN_PROGRESS",
            metadata=parsed_doc.metadata,
        )

        # 3/4. Run chunker.chunk(parsed_doc) -> list[ParsedChunk]
        parsed_chunks = self.chunker.chunk(parsed_doc)

        # 5. Metadata Traceability Enrichment
        chunks = []
        for index, p_chunk in enumerate(parsed_chunks):
            chunk_metadata = p_chunk.metadata.copy()
            # Explicit enriching based on dimension 8 tracking
            chunk_metadata.update(
                {
                    "chunk_index": index,
                    "parser_name": parsed_doc.metadata.get("parser_name", "unknown"),
                    "source_locator": parsed_doc.source_locator,
                    "start_offset": p_chunk.start_offset,
                    "end_offset": p_chunk.end_offset,
                }
            )

            # Flatten additional source metadata into the chunk for easier retrieval filtering
            source_meta = parsed_doc.metadata.get("source_metadata", {})
            chunk_metadata.update(source_meta)

            chunk = Chunk(
                document_id=document.id,
                content=p_chunk.text,
                source_type="file",
                source_category=source_category,
                file_type=file_type,
                status="COMPLETED",
                metadata=chunk_metadata,
            )
            chunks.append(chunk)

        document.chunks = chunks
        document.status = "COMPLETED"

        # 6. Generate Embeddings for all chunks
        chunk_texts = [c.content for c in chunks]
        embeddings = self.embedding_engine.embed_batch(chunk_texts)
        for i, chunk in enumerate(chunks):
            chunk.embedding = embeddings[i]

        # 7. Persist the Document (Metadata) and Chunks (VectorStore)
        self.document_repository.save(document)
        self.vector_store.add_chunks(chunks)

        return document
