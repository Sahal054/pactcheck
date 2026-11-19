import json
import re
from pathlib import Path
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from app.config import settings
from app.services.ai.embeddings import get_embedding_service


class HybridRetriever:
    def __init__(self, index_dir: str = "./data/indexes", load_existing: bool = True):
        self.path = Path(index_dir)
        self.path.mkdir(parents=True, exist_ok=True)
        self.faiss_path = self.path / "playbook.faiss"
        self.meta_path = self.path / "chunks.json"
        self.config_path = self.path / "embedding_config.json"
        self.embedder = get_embedding_service()
        self.chunks = []
        self.index = None
        self.bm25 = None
        if load_existing:
            self.load()

    def build(self, chunks: list[dict]):
        if not chunks:
            raise ValueError("Cannot build an empty playbook index")
        texts = [c["text"] for c in chunks]
        vectors = self.embedder.embed(texts)
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.chunks = chunks
        faiss.write_index(self.index, str(self.faiss_path))
        self.meta_path.write_text(json.dumps(chunks, indent=2), encoding="utf-8")
        self.config_path.write_text(
            json.dumps(
                {
                    **self.embedder.fingerprint(),
                    "dimensions": int(vectors.shape[1]),
                    "normalized": True,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self._build_bm25()

    def _build_bm25(self):
        tokens = [re.findall(r"[a-z0-9]+", c["text"].lower()) for c in self.chunks]
        self.bm25 = BM25Okapi(tokens) if tokens else None

    def load(self):
        if self.faiss_path.exists() and self.meta_path.exists():
            saved = (
                json.loads(self.config_path.read_text())
                if self.config_path.exists()
                else {}
            )
            if saved and saved != {
                **self.embedder.fingerprint(),
                "dimensions": saved.get("dimensions"),
                "normalized": True,
            }:
                raise RuntimeError(
                    "Embedding model mismatch. Rebuild the playbook index before retrieval."
                )
            self.index = faiss.read_index(str(self.faiss_path))
            self.chunks = json.loads(self.meta_path.read_text())
            if (
                not saved
                or self.index.d != saved.get("dimensions")
                or self.index.ntotal != len(self.chunks)
            ):
                raise RuntimeError(
                    "Invalid index metadata. Rebuild the playbook index."
                )
            self._build_bm25()

    def search(
        self, query: str, top_k: int | None = None, document_type: str | None = None
    ) -> list[dict]:
        # OpenMP limits are thread-local; executor threads must set their own limit.
        faiss.omp_set_num_threads(1)
        if self.index is None or not self.chunks:
            raise RuntimeError(
                "Playbook is not indexed. Upload/index the playbook first."
            )
        k = top_k or settings.faiss_top_k
        if k < 1:
            raise ValueError("top_k must be positive")
        q = self.embedder.embed([query])
        if q.shape[1] != self.index.d:
            raise RuntimeError(
                "Embedding dimension mismatch. Rebuild the playbook index."
            )
        eligible = {
            i
            for i, chunk in enumerate(self.chunks)
            if not document_type
            or document_type.upper()
            in chunk.get("applicable_documents", [document_type.upper()])
        }
        scores, ids = self.index.search(q, len(self.chunks))
        dense = [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i >= 0]
        token_scores = self.bm25.get_scores(re.findall(r"[a-z0-9]+", query.lower()))
        sparse_ids = sorted(eligible, key=lambda i: (-float(token_scores[i]), i))[
            : settings.bm25_top_k
        ]
        rankings = [
            [item for item in dense if item[0] in eligible][
                : max(k, settings.faiss_top_k)
            ],
            [
                (int(i), float(token_scores[i]))
                for i in sparse_ids
                if token_scores[i] > 0
            ],
        ]
        fused = {}
        for ranking in rankings:
            for rank, (idx, _) in enumerate(ranking, start=1):
                fused[idx] = fused.get(idx, 0.0) + 1.0 / (settings.rrf_k + rank)
        ordered = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:k]
        return [{**self.chunks[i], "retrieval_score": score} for i, score in ordered]
