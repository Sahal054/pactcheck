# Implementation guide

Core services are split by document parsing/export, AI providers, hybrid retrieval and contract analysis. FastAPI routes orchestrate those services; React uses the typed API client and shared current report.

- Parser bodies begin after heading matches. DOCX body order includes tables; PDF page text is retained for source ranges.
- Embeddings prefer cached MiniLM and use signed SHA-256 token/bigram hashing when unavailable. Fingerprints distinguish both implementations.
- Explicit indexing bypasses incompatible old vectors. Retrieval combines FAISS, BM25 and RRF after document eligibility filtering.
- Review concurrently evaluates each clause with all clauses as context. Pydantic schemas and post-processing constrain evidence, drafting and risk labels.
- Coverage maps applicable mandatory rules to substantive clause roles and assessments. Dependencies match headings first to avoid body cross-reference confusion.
- Report scoring is deterministic and versioned. JSON writes use atomic replacement. Original assessment scores are retained after user drafting choices.
- Word export uses native OOXML insertions/deletions with PactCheck AI authorship and user state handling, plus coverage and interaction sections.
- Revision matching reserves known headings before falling back to numbers; vendor clauses receive a fresh policy review. Added/removed text remains visible.
- The frontend implements review, rules, coverage, revision and settings views with loading, empty and error states. Current review data survives navigation.

Run the backend suite and frontend build before changing interfaces. Ground-truth labels live outside the reviewer, in `sample_data/ground_truth.json`. Model API tests use fakes; runtime keys and user reports are isolated from the test suite. See TESTING_GUIDE.md for reproducible evaluation definitions and ARCHITECTURE.md for score weights.
