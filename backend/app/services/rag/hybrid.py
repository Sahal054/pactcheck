import json
from pathlib import Path
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from app.config import settings
from app.services.ai.embeddings import EmbeddingService

class HybridRetriever:
    def __init__(self, index_dir: str = "./data/indexes"):
        self.path = Path(index_dir)
        self.path.mkdir(parents=True, exist_ok=True)
        self.faiss_path = self.path / "playbook.faiss"
        self.meta_path = self.path / "chunks.json"
        self.config_path = self.path / "embedding_config.json"
        self.embedder = EmbeddingService()
        self.chunks = []
        self.index = None
        self.bm25 = None
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
        self.config_path.write_text(json.dumps({**self.embedder.fingerprint(), "dimensions": int(vectors.shape[1]), "normalized": True}, indent=2), encoding="utf-8")
        self._build_bm25()

    def _build_bm25(self):
        tokens = [c["text"].lower().split() for c in self.chunks]
        self.bm25 = BM25Okapi(tokens) if tokens else None

    def load(self):
        if self.faiss_path.exists() and self.meta_path.exists():
            saved = json.loads(self.config_path.read_text()) if self.config_path.exists() else {}
            if saved and saved != {**self.embedder.fingerprint(), "dimensions": saved.get("dimensions"), "normalized": True}:
                raise RuntimeError("Embedding model mismatch. Rebuild the playbook index before retrieval.")
            self.index = faiss.read_index(str(self.faiss_path))
            self.chunks = json.loads(self.meta_path.read_text())
            self._build_bm25()

    def search(self, query: str, top_k: int | None = None) -> list[dict]:
        if self.index is None or not self.chunks:
            raise RuntimeError("Playbook is not indexed. Upload/index the playbook first.")
        k = top_k or settings.faiss_top_k
        q = self.embedder.embed([query])
        scores, ids = self.index.search(q, min(k, len(self.chunks)))
        dense = [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i >= 0]
        token_scores = self.bm25.get_scores(query.lower().split())
        sparse_ids = np.argsort(token_scores)[::-1][:min(settings.bm25_top_k, len(self.chunks))]
        rankings = [dense, [(int(i), float(token_scores[i])) for i in sparse_ids]]
        fused = {}
        for ranking in rankings:
            for rank, (idx, _) in enumerate(ranking, start=1):
                fused[idx] = fused.get(idx, 0.0) + 1.0 / (settings.rrf_k + rank)
        ordered = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:k]
        return [{**self.chunks[i], "retrieval_score": score} for i, score in ordered]
