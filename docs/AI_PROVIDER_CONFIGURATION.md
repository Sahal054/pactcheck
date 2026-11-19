# AI provider configuration

Defaults: `LLM_PROVIDER=mock`, `EMBEDDING_PROVIDER=local`. Existing `.env` values override defaults; they are never rewritten by Settings.

| Purpose | Providers | Behavior |
|---|---|---|
| Clause review | mock | Deterministic six-rule heuristic; no remote request |
| Clause review | openai | Official OpenAI endpoint, sync/async Pydantic Structured Outputs |
| Clause review | openrouter | Configured base URL/model, JSON validation and fence stripping |
| Embeddings | local | Cached MiniLM, or versioned signed token/bigram 384-dimension fallback |
| Embeddings | openai | OPENAI_API_KEY and OPENAI_EMBEDDING_MODEL |
| Embeddings | openrouter | OPENROUTER_API_KEY and an explicit compatible OPENROUTER_EMBEDDING_MODEL |

The default OpenRouter base URL is `https://openrouter.ai/api/v1`. HTTPS verification is enabled. Clients have timeouts, limited retries and are closed after requests. Provider errors never become compliant assessments.

Set `LOCAL_EMBEDDING_ALLOW_DOWNLOAD=true` to enable model download; the default only uses cached model files and immediately selects the offline fallback when unavailable. The selected implementation is visible in embedding diagnostics and saved fingerprints.

Settings supports runtime provider/model/key changes, then Test LLM Connection and Test Embeddings. Blank key fields preserve existing keys. Keys are returned only as configured/not-configured flags. Runtime changes apply to the current backend process; configure `.env` for restart persistence.

Rebuild the playbook index after changing embedding models/providers. Index fingerprints reject incompatible vectors. Startup rebuilds an incompatible local index using active saved rule chunks. Local/mock latency is tested separately from remote inference; remote speed and availability depend on the selected service.
