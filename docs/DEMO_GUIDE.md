# Demo guide

1. Start the backend from `backend/` and Vite from `frontend/`. For a credential-free demo, choose mock review and local embeddings. Startup prepares the default playbook index.
2. Open Overview, confirm API/index status, and upload `sample_data/Sample_High_Risk_MSA.txt` as MSA.
3. Run review: seven clauses, five High and two Low clause findings. Show readiness, the missing termination rule and the indemnity/liability interaction. Coverage warnings remain separate from clause findings.
4. Filter High risks, inspect the inline diff and split view, expand retrieved evidence, and copy the counsel email. Accept one redline, edit another and reject a third.
5. Export Word and inspect native Track Changes, user choices, executive scorecard, missing-rule section and cross-clause section.
6. Open Playbook Rules; search RULE_002, filter NDA and inspect policy/fallback/escalation details.
7. Open Cross-Clause & Coverage; the current report remains available across navigation.
8. Open Revision Comparison; compare the high-risk MSA against `Sample_MSA.txt`. Liability/IP/confidentiality/indemnity/governing-law changes resolve under the fixture policy, and the termination addition is visible.
9. Open Settings and run both diagnostics. Mock LLM tests explicitly report that no remote request was made; local embedding diagnostics show MiniLM or the hashing implementation.
10. Run `pytest -v -s` to display the benchmark and `npm run build` for the production build.

Mock mode is a deterministic demo reviewer. For a live model demo, configure a real provider/model/key and test connectivity in advance. The bundled data contains 20 clauses across all three contracts. The default NDA playbook also requires liability/governing law, so its missing-rule checklist can show gaps while its five existing clauses remain Low.
