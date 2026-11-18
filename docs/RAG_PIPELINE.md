# Custom Hybrid RAG

## Indexing
- Parse the Legal Negotiation Playbook into rule-level chunks.
- Generate normalized vectors using the configured embedding provider.
- Add vectors to FAISS IndexFlatIP.
- Persist FAISS index and JSON metadata.
- Build BM25Okapi over the same chunks.
- Save embedding provider/model/dimension metadata.

## Querying
- Embed one contract clause using the same model as indexing.
- Run dense FAISS search.
- Run BM25 keyword search.
- Combine ranks with RRF: `score(d) = sum(1 / (k + rank_i(d)))`, with k=60 by default.
- Return top evidence chunks with rule IDs and source references.

Raw cosine and BM25 scores are not directly added because their scales differ. The initial retriever uses rank fusion. Reranking is optional and disabled by default.

## Safety
If no relevant evidence is returned, do not ask the LLM to invent a policy. Return Unclear / Needs Legal Review. Never classify missing evidence as Low risk.
