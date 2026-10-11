import hashlib
import numpy as np
import logging
from typing import List
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER.lower()
        self.dimension = settings.VECTOR_DIMENSION
        self._model = None

        if self.provider == "sentence_transformers":
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
                logger.info(f"Loaded local SentenceTransformer model: {settings.EMBEDDING_MODEL}")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({e}). Falling back to deterministic local embedding.")
                self.provider = "local"

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings into vectors."""
        if not texts:
            return []

        if self.provider == "sentence_transformers" and self._model is not None:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()

        if self.provider == "openai" and settings.EMBEDDING_API_KEY:
            try:
                import httpx
                headers = {"Authorization": f"Bearer {settings.EMBEDDING_API_KEY}"}
                response = httpx.post(
                    "https://api.openai.com/v1/embeddings",
                    headers=headers,
                    json={"input": texts, "model": settings.EMBEDDING_MODEL or "text-embedding-3-small"},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return [item["embedding"] for item in data["data"]]
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}. Falling back to local deterministic embedding.")

        # Local deterministic semantic feature hash projection
        # This guarantees 100% testable, reproducible, normalized embeddings
        # without external API costs or download failures.
        results = []
        for text in texts:
            vec = self._compute_feature_projection(text, self.dimension)
            results.append(vec)
        return results

    def _compute_feature_projection(self, text: str, dim: int) -> List[float]:
        """
        Deterministic, n-gram bag-of-words pseudo-embedding projected onto unit sphere.
        Words and tokens map to repeatable vector representations so similar texts
        have high cosine similarity.
        """
        tokens = [t.lower().strip() for t in text.split() if t.strip()]
        if not tokens:
            return [0.0] * dim

        vector = np.zeros(dim, dtype=np.float32)
        for i, token in enumerate(tokens):
            # Generate deterministic hash seeds
            seed = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            np.random.seed(seed % (2**32))
            token_vec = np.random.normal(0, 1, dim).astype(np.float32)
            # Position decay
            weight = 1.0 / (1.0 + 0.05 * i)
            vector += weight * token_vec

        # Normalize to unit vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

embedding_service = EmbeddingService()
