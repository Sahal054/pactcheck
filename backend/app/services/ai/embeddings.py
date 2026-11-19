"""Normalized embeddings with an explicitly fingerprinted, offline-safe local fallback."""

import hashlib
import logging
import os
import re
from functools import lru_cache
from threading import RLock

for _key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_key, "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "3")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "5")

import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)
HASH_MODEL = "signed-token-bigram-sha256-v1-384"


class EmbeddingService:
    def __init__(self):
        self.provider = settings.embedding_provider.lower()
        self.model_name = (
            settings.local_embedding_model
            if self.provider == "local"
            else (
                settings.openai_embedding_model
                if self.provider == "openai"
                else settings.openrouter_embedding_model
            )
        )
        self._model = None
        self._initialized = False
        self._lock = RLock()

    def _local_model(self):
        with self._lock:
            if not self._initialized:
                try:
                    import torch

                    torch.set_num_threads(1)
                    try:
                        torch.set_num_interop_threads(1)
                    except RuntimeError:
                        pass
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(
                        self.model_name,
                        device="cpu",
                        local_files_only=not settings.local_embedding_allow_download,
                    )
                except Exception as exc:
                    logger.warning(
                        "MiniLM unavailable (%s); using deterministic local feature hashing",
                        type(exc).__name__,
                    )
                self._initialized = True
        return self._model

    @staticmethod
    def _hash_embed(texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), 384), dtype="float32")
        for row, text in enumerate(texts):
            tokens = re.findall(r"[a-z0-9]+", text.lower())
            features = tokens + [f"{a}:{b}" for a, b in zip(tokens, tokens[1:])]
            for feature in features:
                digest = hashlib.sha256(feature.encode("utf-8")).digest()
                vectors[row, int.from_bytes(digest[:4], "little") % 384] += (
                    1 if digest[4] & 1 else -1
                )
        return vectors / np.maximum(
            np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12
        )

    def embed(self, texts: list[str]) -> np.ndarray:
        if self.provider == "local":
            model = self._local_model()
            if not texts:
                return np.empty((0, 384), dtype="float32")
            if model is None:
                return self._hash_embed(texts)
            with self._lock:
                return np.asarray(
                    model.encode(
                        texts,
                        convert_to_numpy=True,
                        normalize_embeddings=True,
                        show_progress_bar=False,
                    ),
                    dtype="float32",
                )
        if self.provider not in ("openai", "openrouter"):
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
        from openai import OpenAI

        key = (
            settings.openai_api_key
            if self.provider == "openai"
            else settings.openrouter_api_key
        )
        if not key or not self.model_name:
            raise RuntimeError(
                f"{self.provider} embeddings require an API key and explicit embedding model"
            )
        if not texts:
            return np.empty((0, 0), dtype="float32")
        kwargs = {"api_key": key, "timeout": 20, "max_retries": 1}
        if self.provider == "openrouter":
            kwargs["base_url"] = settings.openrouter_base_url
        with OpenAI(**kwargs) as client:
            response = client.embeddings.create(model=self.model_name, input=texts)
        vectors = np.asarray(
            [item.embedding for item in sorted(response.data, key=lambda x: x.index)],
            dtype="float32",
        )
        return vectors / np.maximum(
            np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12
        )

    def fingerprint(self) -> dict:
        if self.provider == "local":
            model = self.model_name if self._local_model() is not None else HASH_MODEL
        else:
            model = self.model_name
        return {"provider": self.provider, "model": model}


@lru_cache(maxsize=1)
def get_embedding_service():
    return EmbeddingService()
