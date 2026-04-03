from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from data_layer_manager.domain.schemas.parsed_document import ParsedDocument


class BaseParser(ABC):
    """
    Abstract base class for all parsers in the data layer.
    """

    @abstractmethod
    def parse(
        self, source: bytes | str | Path, source_metadata: dict[str, Any]
    ) -> ParsedDocument:
        """
        Parses a raw source into a normalized ParsedDocument.

        Args:
            source: The raw content. Can be a string, bytes, or a Path depending on the parser.
            source_metadata: Metadata collected prior to parsing (e.g., file path, size).

        Returns:
            A normalized ParsedDocument containing the text and structural hints.
        """
        pass
