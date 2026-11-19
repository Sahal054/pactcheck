# Review prompts and guardrails

The clause system prompt in `backend/app/services/analysis/reviewer.py` constrains review to retrieved playbook evidence. Original text and full document context are untrusted data. Definitions, duration, fees and scope are assessed according to their own purpose, with mandatory missing obligations handled in coverage.

Model output follows `LLMClauseEvaluation`: allowed risk/compliance labels, grounded rule IDs, explanation, contract-ready replacement text, negotiation action, counsel email and a boolean legal-review flag. OpenAI uses SDK structured parsing; OpenRouter responses undergo fence stripping, JSON extraction and the same Pydantic validation.

Post-processing rejects unknown evidence IDs and instruction-style redlines as Unclear / Not Assessed, requiring legal review. It cleans subject lines/salutations from counsel messages and computes word diffs from original body text. Instruction overrides inside vendor content cannot force a Low result.

Negotiation guidance uses retrieved policy/fallback/escalation text. Governing law never receives an invented universally approved jurisdiction. Missing fallback approval remains explicit.

Cross-clause checks are deterministic role/dependency rules, primarily driven by headings. Revision comparison invokes the same reviewer on the vendor revision and uses the resulting compliance to distinguish resolved changes from residual risk. These are implementation boundaries, not claims of unrestricted legal reasoning.
