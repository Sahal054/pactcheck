# File manifest

- `backend/app/`: FastAPI, provider adapters, parsing/export, hybrid retrieval, clause/coverage/interaction analysis and report persistence.
- `backend/tests/`: offline-safe unit, guardrail, adapter, integration, runtime and fixed-label evaluation tests.
- `backend/data/playbook/legal_playbook.md`: six-rule source playbook.
- `backend/data/evaluation_metrics.json`: generated benchmark matrix, metrics and per-clause results.
- `frontend/src/`: React/TypeScript review, policy, coverage, comparison and diagnostics workspaces.
- `sample_data/`: three synthetic contracts and independent ground-truth labels (20 source clauses).
- `docs/`: architecture, scoring, providers, API, RAG, tests, demo and operations guidance.

Virtual environments, node_modules, compiled bundles, private environment files and generated FAISS binaries are ignored. Uploaded documents and reports are local runtime artifacts.
