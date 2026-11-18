# Implementation Guide

Recommended implementation order:
1. Create FastAPI skeleton and configuration.
2. Add document extraction and clause segmentation.
3. Add playbook parser and rule metadata.
4. Add embedding providers and index fingerprint.
5. Add FAISS, BM25 and RRF.
6. Add LLM provider abstraction and structured output validation.
7. Add clause assessment and evidence validation.
8. Add cross-clause detector.
9. Add negotiation scaffolding and revision comparison.
10. Build React dashboard and connect endpoints.
11. Test using synthetic NDA/MSA documents.

The included code is an MVP implementation. Follow README limitations before representing the application as production-grade.
