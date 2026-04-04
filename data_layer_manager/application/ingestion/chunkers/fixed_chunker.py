from data_layer_manager.core.config import ChunkingSettings, get_settings
from data_layer_manager.domain.interfaces.chunker import BaseChunker
from data_layer_manager.domain.schemas.parsed_chunk import ParsedChunk
from data_layer_manager.domain.schemas.parsed_document import ParsedDocument


class FixedSizeChunker(BaseChunker):
    """
    Splits text into chunks of a fixed character size with a specified overlap.
    """

    def __init__(self, settings: ChunkingSettings | None = None):
        if settings is None:
            settings = get_settings().chunking

        self.chunk_size = settings.default_size
        self.overlap = settings.default_overlap

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.overlap < 0:
            raise ValueError("overlap must be non-negative")
        if self.overlap >= self.chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

    def chunk(self, parsed_doc: ParsedDocument) -> list[ParsedChunk]:
        """
        Produce overlapping chunks based strictly on character counts.
        """
        text = parsed_doc.raw_content
        text_length = len(text)

        if text_length == 0:
            return []

        chunks = []
        step = self.chunk_size - self.overlap

        for start_idx in range(0, text_length, step):
            end_idx = min(start_idx + self.chunk_size, text_length)
            chunk_str = text[start_idx:end_idx]

            p_chunk = ParsedChunk(
                text=chunk_str, start_offset=start_idx, end_offset=end_idx, metadata={}
            )
            chunks.append(p_chunk)

            # If we reached the end of the text, stop making chunks
            if end_idx == text_length:
                break

        return chunks
