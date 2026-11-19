# Hackathon engineering guide

The repository contains an end-to-end local demo: intake, parsing, hybrid retrieval, evidence-constrained review, coverage, interactions, negotiation guidance, revision comparison, settings diagnostics and tracked Word export.

For a clean environment, follow README.md to install Python/Node dependencies, start both services and verify the default index. `.env.example` selects credential-free mock/local defaults; existing environment values take precedence.

When extending the application, keep each rule's scope and approved policy in the playbook. Add a labelled fixture and a regression test before changing heuristic behavior. Keep source policy identifiers separate from model-generated drafting, and never convert missing evidence into a Low result.

Demonstrate the high-risk MSA first, then its comparison with the standard MSA. Use the NDA to show that definitions/duration stay Low while document-level omissions remain visible in coverage. All three files contain 20 numbered clauses in total.

Before presenting, run `pytest -v -s` in backend and `npm run build` in frontend. Inspect the generated metrics JSON and explain that perfect fixture scores describe deterministic regression performance, not universal contract/legal accuracy. Live provider access should be tested explicitly in Settings before representing any response as live inference.
