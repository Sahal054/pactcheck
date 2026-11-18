# Troubleshooting

- `ModuleNotFoundError`: activate the backend virtual environment and install `requirements.txt`.
- Local embedding model download fails: check network access; first run downloads model files. Alternatively configure a working remote embedding provider.
- `OPENROUTER_API_KEY is required`: add key to `backend/.env` and restart backend.
- OpenRouter model unavailable/rate limited: choose another currently available model or use mock mode while developing.
- FAISS dimension mismatch: switch back to the index's embedding provider/model or rebuild the index.
- Playbook not indexed: build the index before reviewing a contract.
- Scanned PDF returns no text: OCR is not included in this MVP; use a text-based PDF/DOCX or add OCR.
- CORS/network issue: confirm backend runs at port 8000 and frontend at port 5173.
