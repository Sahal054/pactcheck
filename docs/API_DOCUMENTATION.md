# API Documentation

The backend exposes interactive OpenAPI documentation at `http://127.0.0.1:8000/docs`.

Core routes:
- GET `/api/health`
- GET `/api/settings`
- POST `/api/settings/test-llm`
- POST `/api/settings/test-embeddings`
- POST `/api/playbook/upload`
- POST `/api/playbook/index`
- GET `/api/playbook/index-status`
- POST `/api/contracts/upload`
- POST `/api/review/analyze`
- POST `/api/revisions/compare`
- GET `/api/reports/{review_id}`

The upload endpoint returns a local path. Review and indexing endpoints accept local paths in this prototype; this is intended for local development and must be redesigned before exposing the service to untrusted remote users.
