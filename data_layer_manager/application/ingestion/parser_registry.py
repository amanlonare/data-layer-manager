import logging

from data_layer_manager.domain.interfaces.parser import BaseParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """
    Registry for mapping file extensions to BaseParser implementations.
    Acts as a plug-in factory.
    """

    def __init__(self) -> None:
        self._registry: dict[str, BaseParser] = {}
        self._fallback_parser: BaseParser | None = None

    def register(self, extension: str, parser_instance: BaseParser) -> None:
        """
        Registers a parser instance for a given file extension.

        Args:
            extension: The file extension starting with a dot (e.g. '.md')
            parser_instance: An initialized instance of a BaseParser implementation
        """
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        self._registry[ext] = parser_instance

    def set_fallback(self, parser_instance: BaseParser) -> None:
        """
        Sets a fallback parser for unrecognized extensions.
        """
        self._fallback_parser = parser_instance

    def get_parser(self, extension: str) -> BaseParser:
        """
        Returns the appropriate parser for the extension, or the fallback.
        Raises ValueError if extension is unsupported and no fallback exists.
        """
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"

        parser = self._registry.get(ext)
        if parser is not None:
            return parser

        if self._fallback_parser is not None:
            logger.warning("No specific parser for %s, using fallback.", ext)
            return self._fallback_parser

        raise ValueError(
            f"No parser registered for extension: {ext} and no fallback set."
        )
