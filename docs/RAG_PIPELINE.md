# Hybrid retrieval

The structured Markdown playbook has stable `RULE_###` headings, Policy, Red flags, Preferred wording, Fallback wording, Applicable documents and Escalation fields. Parsing produces rule-level evidence chunks. Unstructured uploads can be indexed as evidence, but do not establish the same approved six-rule policy semantics.

## Index

Normalize vectors and store them in FAISS IndexFlatIP. Persist `chunks.json` and `embedding_config.json` with actual provider/model, dimensions and normalization. MiniLM and signed hashing use distinct fingerprints even though both have 384 dimensions. BM25 indexes the same rule chunks using punctuation-independent word tokens.

Explicit rebuilding bypasses loading an incompatible old index. Retrieval rejects mismatched fingerprints or invalid vector dimensions/chunk counts. Startup creates a missing index or rebuilds incompatible vectors from active saved rule chunks.

## Query

Embed the clause heading and body. Filter eligible rules by their declared document classifications before truncating rankings. Compute dense similarity and BM25 keyword rankings, then fuse with `score(d) = sum(1 / (rrf_k + rank_i(d)))`. Defaults: dense top K 5, sparse top K 5, rrf_k 60. Clause assessments use three evidence chunks.

Dense scores and BM25 scores are never added directly. BM25 zero-score documents do not create artificial sparse rank boosts. Empty classification-filtered results remain empty and require legal review.

The fixture tests assert liability and IP ranking, NDA exclusion of MSA-only rules, all 16 relevant-rule hits at K=3, signed fallback determinism and fingerprint rejection. These measured retrieval results apply to the supplied fixtures.
