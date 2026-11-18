# AI Provider Configuration

| Purpose | Provider | Initial setting |
|---|---|---|
| LLM | OpenRouter | `openrouter` (or `mock` for no-key smoke test) |
| Embeddings | Sentence Transformers local | `local` |
| Future LLM | OpenAI | `openai` |
| Future embeddings | OpenAI | `openai` |

LLM and embedding provider are independent. OpenRouter free chat model routing is not an embeddings endpoint. Configure an explicit OpenRouter embedding model only after verifying it supports embeddings and has zero input pricing.

Switching embedding model requires reindexing all playbook chunks. The app must not mix embeddings from incompatible models.
