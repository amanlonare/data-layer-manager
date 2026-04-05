import logging
from collections.abc import Sequence

from openai import OpenAI, OpenAIError

from data_layer_manager.core.config import get_settings
from data_layer_manager.domain.interfaces.embeddings import BaseEmbeddingEngine

logger = logging.getLogger(__name__)


class OpenAIEmbeddingEngine(BaseEmbeddingEngine):
    """
    OpenAI implementation for embedding generation.
    """

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        batch_size: int | None = None,
    ):
        settings = get_settings().embeddings
        self.model_name = model_name or settings.model_name
        self.batch_size = batch_size or settings.batch_size
        self._dim = settings.dimension

        # Priority to specifically passed api_key, then from settings.
        key = api_key or settings.api_key
        if not key:
            raise ValueError(
                "OpenAI API key must be provided either via OPENAI_API_KEY env or direct initialization."
            )

        self.client = OpenAI(api_key=key)

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(self, text: str) -> list[float]:
        """
        Embeds a single string into a vector.
        """
        try:
            response = self.client.embeddings.create(
                input=[text],
                model=self.model_name,
            )
            return response.data[0].embedding
        except OpenAIError as e:
            logger.error(f"OpenAI embedding failed for text: {e}")
            raise

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Embeds a list of strings efficiently by processing them in chunks (respects batch_size parameter).
        """
        all_embeddings = []
        # Ensure we work with a list for slicing if it's a generic sequence
        text_list = list(texts)
        for i in range(0, len(text_list), self.batch_size):
            batch = text_list[i : i + self.batch_size]
            try:
                response = self.client.embeddings.create(
                    input=list(batch),
                    model=self.model_name,
                )
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)
            except OpenAIError as e:
                logger.error(
                    f"OpenAI embedding failed for batch starting at index {i}: {e}"
                )
                raise

        return all_embeddings
