from app.services.analysis.intelligence import cross_clause_findings
from app.services.rag.playbook import parse_playbook


def test_playbook_rule_parser():
    text = '''## RULE_001 - Liability\nPolicy: Cap liability at 12 months.\nRed flags:\n- Unlimited liability\nPreferred wording: Cap at 12 months.\nApplicable documents: MSA\n'''
    rules = parse_playbook(text)
    assert len(rules) == 1
    assert rules[0]["rule_id"] == "RULE_001"
    assert "12 months" in rules[0]["policy"]


def test_cross_clause_liability_indemnity_flag():
    clauses = [
        {"clause_id": "C1", "heading": "Limitation of Liability", "text": "Liability is capped at fees."},
        {"clause_id": "C2", "heading": "Indemnification", "text": "Indemnity obligations are expressly excluded from the liability cap."}
    ]
    result = cross_clause_findings(clauses, [])
    assert len(result) == 1
    assert result[0]["risk_level"] == "High"
