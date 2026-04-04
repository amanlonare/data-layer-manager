import asyncio
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import cast

from sentence_transformers import SentenceTransformer

from data_layer_manager.core.config import EmbeddingSettings, get_settings
from data_layer_manager.domain.interfaces.embeddings import BaseEmbeddingEngine


class HFEmbeddingEngine(BaseEmbeddingEngine):
    """
    HuggingFace-based embedding engine using local SentenceTransformers models.
    """

    def __init__(self, settings: EmbeddingSettings | None = None):
        """
        Initializes the embedding model.

        Args:
            settings: Configuration settings for the embedding engine.
                      If None, fetches global settings.
        """
        if settings is None:
            settings = get_settings().embeddings

        self._model = SentenceTransformer(settings.model_name)
        # Ensure dimension is an int, fallback to checking a test encode if None
        dim = self._model.get_sentence_embedding_dimension()
        if dim is None:
            # Fallback check
            dim = len(self._model.encode("test"))
        self._dimension = int(dim)
        self._executor = ThreadPoolExecutor(max_workers=4)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """
        Generates an embedding for a piece of text.
        Executes in a ThreadPool to stay async-friendly.
        """
        result = self._model.encode(text)
        return cast(list[float], result.tolist())

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Generates embeddings for multiple pieces of text.
        """
        # Convert Sequence to list to satisfy overloads
        result = self._model.encode(list(texts))
        return cast(list[list[float]], result.tolist())

    async def aembed(self, text: str) -> list[float]:
        """
        Async version of embed.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.embed, text)

    async def aembed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Async version of embed_batch.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.embed_batch, texts)
