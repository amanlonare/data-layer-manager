from abc import ABC, abstractmethod

from data_layer_manager.domain.schemas.parsed_chunk import ParsedChunk
from data_layer_manager.domain.schemas.parsed_document import ParsedDocument


class BaseChunker(ABC):
    """
    Abstract base class for all chunking strategies.
    Takes a ParsedDocument and splits it into rich ParsedChunks.
    """

    @abstractmethod
    def chunk(self, parsed_doc: ParsedDocument) -> list[ParsedChunk]:
        """
        Splits a ParsedDocument into a list of ParsedChunks.

        Args:
            parsed_doc: The normalized extracted document.

        Returns:
            A list of ParsedChunk objects containing text slices and offsets.
        """
        pass
