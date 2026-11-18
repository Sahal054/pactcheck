# ContractIQ — Enterprise Contract Intelligence & Negotiation Platform

ContractIQ is a local-first prototype for reviewing vendor NDAs/MSAs against a company's internal legal negotiation playbook. It includes custom Hybrid RAG (FAISS + BM25 + Reciprocal Rank Fusion), provider adapters for OpenRouter/OpenAI, local embeddings, clause assessment, a first-pass cross-clause detector, negotiation guidance, and a basic revision comparison workflow.

> **Legal disclaimer:** This is an AI-assisted prototype, not legal advice. All findings, redlines and negotiation positions require review by qualified legal professionals.

## Current implementation status

| Module | Status |
|---|---|
| FastAPI backend | Implemented |
| React dashboard | Implemented (MVP) |
| PDF/DOCX/TXT extraction | Implemented; scanned PDF OCR not included |
| Playbook parser and indexing | Implemented for structured Markdown; PDF/text fallback |
| FAISS + BM25 + RRF | Implemented |
| Local/OpenRouter/OpenAI LLM adapters | Implemented; live calls require credentials and provider/model availability |
| Local/OpenRouter/OpenAI embeddings | Implemented; OpenRouter requires a compatible embedding model ID |
| Clause assessment | Implemented; mock mode is explicitly heuristic |
| Cross-clause intelligence | Implemented as a deterministic first-pass pattern detector |
| Negotiation strategy | Basic playbook-grounded scaffold |
| Revision comparison | Basic clause matching/text comparison; semantic re-assessment is future work |
| Missing clause checklist | Not yet exposed as a complete UI workflow |
| Playbook conflict detection | Not yet implemented |
| Automated full-stack tests | Partial backend unit tests included |

## Requirements
- Python 3.11+
- Node.js 20+
- Internet connection for installing dependencies and downloading the local embedding model the first time
- For live LLM inference: OpenRouter API key or OpenAI API key
- For local mock mode: no API key required

## Run on macOS

Terminal 1:
```bash
cd ContractIQ_Project/backend
cp .env.example .env
# For offline/mock assessment, set LLM_PROVIDER=mock in .env
# For OpenRouter live inference, set LLM_PROVIDER=openrouter and add OPENROUTER_API_KEY
bash start_backend.sh
```

Terminal 2:
```bash
cd ContractIQ_Project/frontend
bash start_frontend.sh
```

Open http://127.0.0.1:5173 and API docs at http://127.0.0.1:8000/docs.

## First-time workflow
1. In the backend `.env`, choose `LLM_PROVIDER=mock` to inspect the application without a live LLM, or `openrouter` for live inference.
2. Keep `EMBEDDING_PROVIDER=local` for zero API embedding cost.
3. In the app's Playbook Index section, use `./data/playbook/legal_playbook.md` and click Build / rebuild index.
4. Upload `../sample_data/Sample_High_Risk_MSA.txt` (or a PDF/DOCX contract) through the UI.
5. Select MSA and run review.

The sample data directory is at the project root. You can also copy sample files into `backend/data/contracts`.

## Provider configuration

### Free-first local embeddings + OpenRouter LLM
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=openrouter/free
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

OpenRouter's free router is subject to model availability and rate limits. Free chat inference does not imply free embeddings. Local Sentence Transformers is the default embedding option and incurs no per-request API charge after model download.

### Mock mode
```env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=local
```
Mock mode is for local plumbing and deterministic demonstration only. It is not a substitute for live model reasoning. In mock mode, the current clause reviewer uses a narrow heuristic and labels the result accordingly.

### Later: OpenAI LLM + OpenAI embeddings
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4.1-mini
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```
OpenAI API usage is paid separately from a ChatGPT subscription. Confirm the model is enabled for your API project.

### Mixed configuration
You can use OpenRouter for LLM calls and OpenAI embeddings, or OpenAI for LLM calls and local embeddings. LLM and embedding providers are configured independently.

**Important:** If the embedding provider or model changes, rebuild the playbook index. The backend checks saved embedding metadata and refuses incompatible index use.

## API endpoints
- `GET /api/health`
- `GET /api/settings`
- `POST /api/settings/test-llm`
- `POST /api/settings/test-embeddings`
- `POST /api/playbook/upload`
- `POST /api/playbook/index` (multipart `path` field)
- `GET /api/playbook/index-status`
- `POST /api/contracts/upload`
- `POST /api/review/analyze` (multipart `path`, `document_type`)
- `POST /api/revisions/compare` (multipart `original_path`, `revised_path`)
- `GET /api/reports/{review_id}`

For a quick API test, use Swagger at `/docs`.

## Run tests
```bash
cd backend
source .venv/bin/activate
pytest -q
```

## Important limitations to address before a competition demo
1. The current heading-based parser is a baseline. It does not reliably handle every contract layout, tables, scanned PDFs or complex multilevel numbering.
2. Cross-clause analysis currently detects a narrow liability/indemnity pattern using deterministic text matching. It is not yet a general legal reasoning engine.
3. Revision comparison currently matches by clause number/heading and detects text changes. It does not yet perform a full second-pass semantic risk assessment on revised clauses.
4. Risk scoring is clause-level and should be expanded with a documented, calibrated scoring policy.
5. Settings are configured through backend `.env`; a secure runtime settings editor is not yet implemented.
6. Mock mode does not perform genuine LLM analysis.
7. OCR for image-only PDFs is not included.

These limitations are deliberately disclosed rather than presented as completed features.
