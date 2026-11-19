# PactCheck / ContractIQ

Vendor contract review and redlining against an internal negotiation playbook, built with FastAPI, React, TypeScript and Vite.

## Run locally

Use Python 3.11+ and Node.js 20+. From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Interactive API documentation is at http://127.0.0.1:8000/docs.

## Implemented workspaces

- **Overview / Contract Review:** PDF, DOCX, Markdown and TXT intake; MSA, NDA, DPA, SOW and SLA classification; playbook upload/indexing; readiness scoring; clause redlines; inline and split diffs; accept/edit/reject; evidence drawers; counsel emails; negotiation strategies; native Word Track Changes export.
- **Playbook Rules:** live indexed policy, red flags, escalation/fallback positions, search, document filtering and copy wording.
- **Cross-Clause & Coverage:** missing mandatory rules and clause interactions, sharing the current review across views.
- **Revision Comparison:** original/revised uploads, revised-clause policy re-assessment, changes, removals and additions.
- **Settings & Diagnostics:** runtime provider/model/key editing and independent LLM/embedding connection tests. Keys are never returned by settings endpoints.

## Offline and live providers

The defaults are `LLM_PROVIDER=mock` and `EMBEDDING_PROVIDER=local`. Mock review uses deterministic policy heuristics for all six supplied rules; it is explicitly identified in every assessment.

Local embeddings use cached `sentence-transformers/all-MiniLM-L6-v2`. If it cannot load, a deterministic signed token and bigram hashing implementation produces normalized 384-dimensional vectors. No download is attempted by default. Set `LOCAL_EMBEDDING_ALLOW_DOWNLOAD=true` to permit initial model download. Fallback vectors have their own versioned fingerprint and never silently share an index with MiniLM vectors.

Startup creates a missing default index. A startup embedding mismatch rebuilds the index from the active saved rule chunks. Explicit index rebuild also works after changing providers/models. During a running session, incompatible retrieval fails with a rebuild instruction.

For live review, select `openai` or `openrouter`, provide the corresponding API key and model, then test the connection in Settings. OpenAI requests use the official endpoint and Pydantic Structured Outputs. OpenRouter uses its configured base URL and handles fenced JSON. TLS verification remains enabled. Live response latency depends on the provider; only warm local/mock assessment has a tested sub-three-second threshold.

## Policy coverage and scoring

The supplied six rules govern liability, IP ownership, confidentiality, termination, indemnification and governing law. Each rule declares its applicable classifications; DPA/SOW/SLA uploads work but need additional applicable playbook rules for substantive assessment. The existing NDA rules include liability and governing law, even when the sample NDA omits them.

Coverage is distinct from per-clause compliance: a definition is not penalized for missing obligations belonging elsewhere, while a completely absent mandatory rule appears in the coverage checklist. Readiness is a deterministic 0–100 snapshot of the original contract using 60% clause findings, 25% mandatory coverage and 15% cross-clause interactions. Accepting or editing a proposed redline does not certify the vendor contract as compliant. See [architecture](docs/ARCHITECTURE.md) for the exact formula.

## Verification

```bash
cd backend
source .venv/bin/activate
pytest -v -s
cd ../frontend
npm run build
```

The backend suite includes parsing and page tracking, offline embedding fallback, FAISS/BM25/RRF ranking and filtering, fingerprint validation, OOXML track changes, evidence guardrails, sync/async provider adapters, real cached-local embedding execution, concurrent review, API workflows and a fixed-label sample benchmark.

Ground truth is in `sample_data/ground_truth.json`. The supplied contracts contain **20 numbered clauses (7 + 8 + 5)**. The benchmark evaluates all of them and saves `backend/data/evaluation_metrics.json`. A positive means a clause-level policy deviation; missing clauses and cross-clause dependencies are measured separately. Perfect scores on these small deterministic fixtures do not measure general legal accuracy or live provider quality.

## Operating boundaries

This is a local enterprise-hackathon application. API paths accept backend-accessible files and runtime settings apply to the backend process, so bind to localhost. API keys live in process memory or your private `.env`; runtime edits do not rewrite that file. Authentication and multi-tenant isolation are outside this local deployment.

Text-based PDFs are supported; scanned image-only PDFs return an explicit OCR-required error. PDF pages are tracked directly. DOCX has no fixed pagination without a layout engine, so page tracking follows explicit/rendered Word page breaks; otherwise page 1 is reported. Cross-clause checks and offline review are deterministic heuristics. All legal findings and drafting proposals require qualified legal review.
