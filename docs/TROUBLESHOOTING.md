# Troubleshooting

- **Missing Python package:** activate `backend/.venv` and install `requirements.txt`.
- **TypeScript syntax error under Node:** use Node.js 20+ and reinstall frontend dependencies with `npm ci` if necessary.
- **MiniLM unavailable/offline:** local embeddings automatically use deterministic 384-dimensional feature hashing. Diagnostics show the actual implementation. Set `LOCAL_EMBEDDING_ALLOW_DOWNLOAD=true` only when initial model download is desired.
- **Embedding mismatch after settings changes:** rebuild the playbook index. Explicit rebuild works even when the old fingerprint is incompatible. Startup preserves active saved rules when rebuilding incompatible vectors.
- **LLM test fails:** verify provider, model and key in Settings, save, then test. OpenAI uses its official endpoint; OpenRouter uses OPENROUTER_BASE_URL. Mock mode is available without a key.
- **Review is Unclear:** inspect the reason/evidence. Unsupported classifications need applicable playbook rules; provider errors and invalid or ungrounded output require legal review.
- **Missing rule despite Low clause findings:** coverage and clause compliance are separate. A clause cannot stand in for a completely absent mandatory provision.
- **No PDF text:** image-only PDFs need OCR before upload. The parser returns a clear error instead of an empty review.
- **DOCX page numbers differ from Word:** page tracking follows explicit/rendered breaks; automatic layout pagination requires a rendering engine.
- **Settings reset on restart:** runtime settings are process-local. Update private backend/.env for persistent defaults.
- **API offline/CORS:** start the backend on 127.0.0.1:8000 and Vite on localhost:5173 or 127.0.0.1:5173. Set VITE_API_URL if changing the API address.
- **Clipboard blocked:** copy the visible email or clause text manually; the workbench reports the error.
- **Async tests hang in a restricted sandbox:** allow local asyncio thread/event-loop signaling. Even a trivial `asyncio.to_thread` task may stall when that signaling is blocked.
