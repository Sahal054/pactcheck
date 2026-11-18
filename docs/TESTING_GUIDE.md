# Testing Guide

Run from `backend/` after installing requirements:

```bash
pytest -q
```

Included tests cover structured playbook parsing and a liability/indemnification cross-clause pattern. For complete validation, add tests for PDF/DOCX extraction, provider errors, FAISS/BM25 ranking, index fingerprint mismatch, structured LLM output validation and full API workflow.

Live provider tests require credentials and should be run separately. Never report a live provider test as passed unless an actual API response was received.
