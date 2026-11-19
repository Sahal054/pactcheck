# Testing and evaluation

Activate `backend/.venv`, then run `pytest -v -s` from `backend/`. Run `npm run build` from `frontend/` with Node.js 20+.

## Backend coverage

- `test_document_and_rag.py`: TXT/Markdown/PDF/DOCX, table order, multilevel headings, page ranges, empty inputs, MiniLM/fallback behavior, FAISS+BM25+RRF ranking, classification filters, fingerprint mismatch, diff round trips and native Word tracked revisions for all user states.
- `test_reviewer_guardrails.py`: prompt injection, fabricated evidence, instruction-style redlines, all six offline rules, unknown governing law, coverage gaps, role precision, cap exclusion patterns, async concurrency/full context, provider errors and real cached MiniLM execution.
- `test_llm_adapters.py`: sync/async structured parsing, OpenRouter fenced JSON, refusal behavior and client cleanup.
- `test_api_workflow.py`: automatic indexing, health, playbook upload/index/rules, contract upload, analyze, coverage/scoring, report retrieval, edits/rejections, Word download, revised assessment, additions/removals, settings/diagnostics, secret redaction and invalid inputs.
- `test_evaluation_metrics.py`: fixed-label benchmark, printed confusion/metric tables and `backend/data/evaluation_metrics.json`.
- `test_logic.py`: original regression cases retained.

Tests isolate settings, keys, index and report directories from user data. Network APIs are mocked. The offline benchmark always uses deterministic feature hashing; a separate local-runtime test uses cached MiniLM when available and otherwise exercises the real fallback. No live provider test is represented as a genuine network response.

## Benchmark definition

`sample_data/ground_truth.json` independently labels all 20 numbered source clauses: high-risk MSA 7, MSA 8, NDA 5. Positive means a clause policy deviation; supporting clauses remain negative. Missing mandatory provisions are document coverage gaps, not fabricated clause false positives.

The matrix records TP, TN, FP and FN. The metrics are Accuracy, Precision, Recall, F1, Specificity, FPR, FNR and relevant-rule Hit@K=3. The RAG denominator excludes scope/fees clauses without an applicable policy target (16 relevant queries). Every clause must also receive a definite assessment; Unclear cannot be counted as a correct negative.

Cross-clause findings are compared against manually specified relationships per contract. The high-risk MSA must never trigger Liability clause without indemnification. Legitimate return/deletion dependency warnings are evaluated separately from clause compliance.

The fixture assertions require TP=5, TN=15, FP=FN=0, 16/16 rule hits and no unexpected cross-clause findings. This small deterministic benchmark measures regression behavior, not general legal quality or live-model accuracy.

Some restricted execution environments prevent asyncio worker wakeups even for a trivial thread task. Run tests in an environment permitting local thread/event-loop signaling; do not replace async tests with synchronous mocks to conceal that restriction.
