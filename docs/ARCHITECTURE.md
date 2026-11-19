# Architecture

The local FastAPI API persists uploaded documents, playbook vectors and report JSON under `backend/data`. React shares the current report between review and cross-clause views. Settings hold runtime provider configuration in the backend process.

## Review data flow

1. Extract PDF pages or ordered DOCX paragraphs/tables, Markdown or TXT.
2. Slice each numbered/Markdown heading from its body, preserving page locations.
3. Retrieve document-applicable playbook evidence using normalized FAISS similarity, BM25 and reciprocal rank fusion.
4. Evaluate clauses concurrently with `asyncio.gather`. Blocking retrieval runs in worker threads. Every model prompt includes the full document context and treats vendor content as untrusted data.
5. Validate model schemas and evidence IDs. Reject fabricated rule references and instruction-style replacements; uncertain/provider-failed results require legal review.
6. Build rule coverage, clause interactions, negotiation strategies and deterministic readiness.
7. Persist the report atomically. Accept/edit/reject updates preserve the original analysis snapshot; export uses the latest user-selected text and states.
8. Revisions are matched by heading before number, and revised clauses receive a fresh policy assessment. Additions and removals remain visible.

## Readiness version 1.0

Clause risk weights: Low = 0, Medium = 0.5, High = 1, Unclear = 0.75. `C` is their average.

Coverage gap weights: Covered = 0, Partially Covered = 0.5, Not Covered = 1. `G` is their average.

`I` is the sum of cross-clause risk weights, capped at 1.

`score = round(100 * (1 - 0.60*C - 0.25*G - 0.15*I))`, bounded to 0–100. With no applicable mandatory policy coverage, score is 0.

Overall risk is High if any clause/interaction is High or any mandatory rule is absent; otherwise Medium for Medium/Unclear findings, partial coverage or no policy coverage; otherwise Low. These are deterministic triage outputs rather than calibrated probabilities.

## Source and trust boundaries

The playbook supplies policy text, evidence identifiers, approved preferred positions and escalation requirements. Model output cannot invent policy evidence or a universally approved governing jurisdiction. Supporting definitions/duration clauses do not need to restate substantive obligations. Mandatory gaps are evaluated separately.

Embedding indexes persist the actual implementation fingerprint, dimensions and normalization. A hashing fallback cannot load MiniLM vectors or vice versa. Startup reindexes active rule chunks on incompatibility. Normal retrieval requires an explicit rebuild when runtime provider settings change.

This is a localhost single-process workflow. Settings are runtime scoped, JSON files are atomically replaced, and user API secrets are never returned. Scanned PDF OCR, authentication, tenancy and general legal reasoning are not implied by the deterministic checks.
