
import os

# Limit native-library threading to reduce CPU threading conflicts.
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import numpy as np
from app.config import settings


class EmbeddingService:
    """Local Sentence Transformers or optional OpenAI/OpenRouter embeddings."""

    def __init__(self):
        self.provider = settings.embedding_provider.lower()
        self.model_name = settings.local_embedding_model
        self._model = None

    def _local_model(self):
        if self._model is None:
            import torch

            torch.set_num_threads(1)

            try:
                torch.set_num_interop_threads(1)
            except RuntimeError:
                pass

            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.model_name,
                device="cpu"
            )

        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        """Convert a list of text chunks into normalized embeddings."""

        if not texts:
            return np.empty((0, 0), dtype="float32")

        if self.provider == "local":
            vectors = self._local_model().encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            return np.asarray(vectors, dtype="float32")

        if self.provider in ("openai", "openrouter"):
            from openai import OpenAI

            if self.provider == "openai":
                if not settings.openai_api_key:
                    raise RuntimeError(
                        "OPENAI_API_KEY is required for OpenAI embeddings"
                    )

                client = OpenAI(
                    api_key=settings.openai_api_key
                )
                model = settings.openai_embedding_model

            else:
                if (
                    not settings.openrouter_api_key
                    or not settings.openrouter_embedding_model
                ):
                    raise RuntimeError(
                        "OpenRouter embeddings require an API key "
                        "and an explicit embedding model"
                    )

                client = OpenAI(
                    api_key=settings.openrouter_api_key,
                    base_url=settings.openrouter_base_url
                )
                model = settings.openrouter_embedding_model

            response = client.embeddings.create(
                model=model,
                input=texts
            )

            vectors = np.asarray(
                [item.embedding for item in response.data],
                dtype="float32"
            )

            norms = np.linalg.norm(
                vectors,
                axis=1,
                keepdims=True
            )

            return vectors / np.maximum(norms, 1e-12)

        raise ValueError(
            f"Unsupported embedding provider: {self.provider}"
        )

    def fingerprint(self) -> dict:
        """Identify the embedding provider and model."""

        if self.provider == "local":
            return {
                "provider": "local",
                "model": self.model_name
            }

        if self.provider == "openai":
            return {
                "provider": "openai",
                "model": settings.openai_embedding_model
            }

        if self.provider == "openrouter":
            return {
                "provider": "openrouter",
                "model": settings.openrouter_embedding_model
            }

        raise ValueError(
            f"Unsupported embedding provider: {self.provider}"
        )


@__import__("functools").lru_cache(maxsize=1)
def get_embedding_service():
    return EmbeddingService()
