# API documentation

Run the backend on localhost:8000; use `/docs` for complete request schemas. File operations accept backend-accessible local paths. Upload first to receive a path.

| Method | Endpoint | Request / behavior |
|---|---|---|
| GET | `/api/health` | Process health and active providers |
| GET | `/api/settings` | Providers/models and key-presence booleans; no secrets |
| POST | `/api/settings` | JSON: llm_provider, llm_model, embedding_provider, embedding_model, openai_api_key, openrouter_api_key; all optional |
| POST | `/api/settings/test-llm` | Connection result; mock explicitly makes no remote request |
| POST | `/api/settings/test-embeddings` | Dimensions and actual embedding model fingerprint |
| POST | `/api/playbook/upload` | Multipart `file`: md, txt, pdf, docx |
| POST | `/api/playbook/index` | Multipart `path`; replaces index, including incompatible existing indexes |
| GET | `/api/playbook/index-status` | Index existence, rule count and default playbook path |
| GET | `/api/playbook/rules` | Indexed structured rule records |
| POST | `/api/contracts/upload` | Multipart `file`: pdf, docx, md, txt |
| POST | `/api/review/analyze` | Multipart `path`, `document_type` (default MSA) |
| GET | `/api/reports/{review_id}` | Persisted full report |
| PATCH | `/api/reports/{review_id}/clauses/{clause_id}` | JSON `redline_status`: pending/accepted/edited/rejected, optional `suggested_redline`; edited requires nonempty text |
| GET | `/api/reports/{review_id}/export-docx` | Word download with native tracked revisions |
| POST | `/api/revisions/compare` | Multipart `original_path`, `revised_path`, `document_type` |

Document classifications: MSA, NDA, DPA, SOW, SLA. Rules apply only to classifications in each rule's metadata. No applicable rules yields Unclear assessments and readiness 0, requiring legal review.

Reports include `created_at`, `contract_readiness_score`, `overall_risk`, `risk_summary`, `clauses`, `rule_coverage`, `cross_clause_findings` and `negotiation_strategies`. Clause records include source page ranges, evidence, body-only replacement text, counsel emails, word diffs and user redline states. Coverage statuses are Covered, Partially Covered and Not Covered.

Comparison statuses: Resolved (Compliant), Changed - Residual Risk (risk level), No Material Text Change, Removed and Added. Revised assessments accompany matched and added clauses; removed clauses have deletion diffs. Heading matches take precedence over clause numbers to tolerate renumbering.

Unknown reports and clauses return 404. Invalid settings, classifications and empty edited replacements return 422. Unsupported uploads, parsing/indexing and provider diagnostic errors return 400. Provider assessment failures become Unclear clause records rather than a false compliant result. Runtime settings are process-local; use `.env` for persistence.
