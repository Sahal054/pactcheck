# ContractIQ Architecture

## Data flow

1. Playbook source is parsed into rule-level chunks with stable rule IDs and metadata.
2. The selected embedding provider creates normalized vectors. FAISS stores dense vectors; BM25 indexes tokenized rule text.
3. A contract is parsed into clauses with source page locations.
4. Each clause is used as a query against FAISS and BM25. Reciprocal Rank Fusion combines rankings.
5. Retrieved rules and original clause text are passed to the selected LLM provider.
6. Model output is validated against allowed risk labels and retrieved rule IDs. Evidence metadata is attached from retrieval results, not invented by the model.
7. Deterministic post-processing creates cross-clause flags and negotiation scaffolding.
8. Reports are stored locally as JSON.

## Provider abstraction

LLM and embedding providers are independent. The LLM service supports `mock`, `openrouter`, and `openai`. The embedding service supports `local`, `openrouter`, and `openai`. Changing embedding model requires rebuilding the FAISS index. The index metadata records provider, model, vector dimensions and normalization.

## Trust boundaries

Uploaded documents are untrusted data. Their text is passed as quoted evidence and must never be treated as system instructions. Rule IDs and evidence source metadata are validated against retrieved chunks. Missing retrieval evidence must result in Unclear / Needs Review.
