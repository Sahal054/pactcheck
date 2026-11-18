# Fresco Play / Six-Hour Rebuild Guide

## Suggested six-hour sequence
- 0:00–0:30: Create FastAPI/React skeleton, environment and health route.
- 0:30–1:15: Implement document parsing, clause extraction and sample data.
- 1:15–2:15: Implement playbook parser, embeddings, FAISS, BM25 and RRF.
- 2:15–3:00: Implement evidence-grounded clause assessment and redline output.
- 3:00–3:45: Implement cross-clause interaction detection and negotiation recommendations.
- 3:45–4:30: Implement revised-version comparison.
- 4:30–5:15: Build dashboard and connect review endpoints.
- 5:15–6:00: Run sample contracts, fix errors, rehearse demo and package.

## Module-generation prompt pattern
“Implement [module] in Python/TypeScript. Follow the existing project interfaces. Do not invent endpoints or schemas. Include input/output types, error handling and tests. Preserve source rule IDs and evidence. Do not leave TODOs for the requested functionality.”

## Demo priority
A reliable end-to-end review with clear evidence is more important than optional modules. If time is short, preserve: upload → extract → hybrid retrieve → assess → show risk/evidence/redline. Demonstrate cross-clause detection as the signature feature. Do not claim unfinished semantic revision comparison as complete.
