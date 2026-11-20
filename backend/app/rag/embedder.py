"""
Ojas Embedding Service.

Provides dense vector embeddings using fastembed (BAAI/bge-small-en-v1.5).
Completely offline, fast CPU inference, 384-dimensional vectors.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Default model name per 09_Implementation_Plan.md §14.2
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384


class Embedder:
    """
    FastEmbed text embedding wrapper with singleton reuse.
    Dimension: 384 (bge-small-en-v1.5).
    """

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        """Initialize the FastEmbed TextEmbedding engine."""
        try:
            from fastembed import TextEmbedding

            logger.info("Initializing embedding model: %s", self.model_name)
            self._model = TextEmbedding(model_name=self.model_name)
            logger.info("Embedding model loaded successfully.")
        except Exception as exc:
            logger.exception("Failed to load FastEmbed model %s: %s", self.model_name, exc)
            self._model = None

    @property
    def is_available(self) -> bool:
        """Return True if embedding model is ready."""
        return self._model is not None

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of text strings into dense vector representations.
        Returns a list of 384-float vectors.
        """
        if not texts:
            return []

        if not self.is_available:
            logger.warning("Embedding model is not available — falling back to zero vectors.")
            return [[0.0] * EMBEDDING_DIMENSION for _ in texts]

        try:
            # fastembed returns a generator of numpy arrays
            raw_embeddings = self._model.embed(texts)
            return [emb.tolist() for emb in raw_embeddings]
        except Exception as exc:
            logger.exception("Error generating embeddings: %s", exc)
            return [[0.0] * EMBEDDING_DIMENSION for _ in texts]

    def embed_single(self, text: str) -> List[float]:
        """Embed a single text string."""
        results = self.embed_texts([text])
        if results:
            return results[0]
        return [0.0] * EMBEDDING_DIMENSION


# Singleton global instance
_global_embedder: Optional[Embedder] = None


def get_embedder() -> Embedder:
    """Return the global Embedder instance."""
    global _global_embedder
    if _global_embedder is None:
        _global_embedder = Embedder()
    return _global_embedder
