from abc import ABC, abstractmethod
from collections.abc import Sequence


class BaseEmbeddingEngine(ABC):
    """
    Abstract base class for all embedding engines.
    Ensures that the architecture can support multiple providers (Local, OpenAI, etc.).
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """The dimensionality of the vectors produced by this engine."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """
        Generates an embedding for a single string of text.

        Args:
            text: The text to be embedded.

        Returns:
            A list of floats representing the embedding vector.
        """

    @abstractmethod
    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Generates embeddings for a batch of strings.

        Args:
            texts: A sequence of strings to be embedded.

        Returns:
            A list of embedding vectors.
        """
