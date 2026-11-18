import re

# Each check: if any clause matches `trigger`, some clause must match `required`.
# `docs` limits the check to certain document types (None = all).
# `exclude_self` means the triggering clause itself does not count as satisfying `required`.
DEPENDENCY_CHECKS = [
    {
        "name": "Termination without return/deletion",
        "trigger": ["terminat"],
        "required": ["return", "delet", "destroy"],
        "docs": None,
        "exclude_self": False,
        "risk": "Medium",
        "explanation": "A termination provision exists but no clause covers return or deletion of information afterwards.",
        "recommendation": "Add a return/deletion obligation that applies on termination or expiry.",
    },
    {
        "name": "Confidentiality without return/deletion",
        "trigger": ["confidential"],
        "required": ["return", "delet", "destroy"],
        "docs": None,
        "exclude_self": False,
        "risk": "Medium",
        "explanation": "Confidentiality obligations exist but no clause covers return or deletion of confidential information.",
        "recommendation": "Add a return/deletion clause, with any backup-retention carve-out limited in scope and duration.",
    },
    {
        "name": "Indemnification without a liability clause",
        "trigger": ["indemn"],
        "required": ["liabilit"],
        "docs": {"MSA"},
        "exclude_self": True,
        "risk": "Medium",
        "explanation": "An indemnification clause exists but no separate limitation of liability clause defines how it interacts with the cap.",
        "recommendation": "Add a liability clause and state whether indemnities sit inside or outside the cap (legal approval needed for any exception).",
    },
    {
        "name": "Liability clause without indemnification",
        "trigger": ["liabilit"],
        "required": ["indemn"],
        "docs": {"MSA"},
        "exclude_self": True,
        "risk": "Medium",
        "explanation": "A liability clause exists but the agreement has no indemnification clause.",
        "recommendation": "Confirm whether vendor indemnification is required by the playbook and add it if so.",
    },
]

CAP_EXCLUSION_PATTERNS = [
    "excluded from the liability cap",
    "not subject to the liability cap",
    "outside the limitation of liability",
    "without limitation",
]


def _text(clause: dict) -> str:
    return f"{clause.get('heading', '')} {clause.get('text', '')}".lower()


def _matches(clause: dict, terms: list) -> bool:
    t = _text(clause)
    return any(term in t for term in terms)


def cross_clause_findings(
    clauses: list,
    assessments: list,
    coverage: list | None = None,
    document_type: str = "MSA",
) -> list:
    findings = []

    def add(related, risk, relationship, explanation, recommendation, basis):
        findings.append({
            "finding_id": f"CROSS_{len(findings) + 1:03d}",
            "related_clause_ids": related,
            "risk_level": risk,
            "relationship": relationship,
            "explanation": explanation,
            "recommendation": recommendation,
            "requires_legal_review": True,
            "basis": basis,
        })

    # 1. Liability cap vs indemnification exception (MSA only)
    if document_type.upper() == "MSA":
        liability = [c for c in clauses if _matches(c, ["liabilit"])]
        indemnity = [c for c in clauses if _matches(c, ["indemn"])]
        for l in liability:
            for ind in indemnity:
                if l["clause_id"] == ind["clause_id"]:
                    continue
                combined = f"{l['text']} {ind['text']}".lower()
                if any(p in combined for p in CAP_EXCLUSION_PATTERNS):
                    add(
                        [l["clause_id"], ind["clause_id"]],
                        "High",
                        "Liability cap and indemnification exception",
                        "The agreement appears to exclude indemnification obligations from the general liability cap. "
                        "This may create exposure beyond the stated cap and should be reviewed as a combined provision.",
                        "Clarify whether indemnification obligations are subject to an agreed cap and obtain legal approval for any exception.",
                        "Deterministic text-pattern flag; confirm against the full clauses and playbook.",
                    )

    # 2. Dependency checks (missing companion clauses)
    for check in DEPENDENCY_CHECKS:
        if check["docs"] and document_type.upper() not in check["docs"]:
            continue
        triggers = [c for c in clauses if _matches(c, check["trigger"])]
        if not triggers:
            continue
        satisfied = False
        for c in clauses:
            if check["exclude_self"] and c in triggers:
                continue
            if _matches(c, check["required"]):
                satisfied = True
                break
        if not satisfied:
            add(
                [c["clause_id"] for c in triggers],
                check["risk"],
                check["name"],
                check["explanation"],
                check["recommendation"],
                "Deterministic keyword dependency check; confirm against the full document.",
            )

    # 3. Playbook rules the document as a whole does not (fully) satisfy
    risk_for = {"Not Covered": "High", "Partially Covered": "Medium", "Unclear": "Unclear"}
    for row in coverage or []:
        status = row.get("coverage_status")
        if status in risk_for:
            add(
                row.get("satisfying_clause_ids", []),
                risk_for[status],
                f"Playbook rule coverage: {row['rule_id']} ({status})",
                row.get("gap") or f"{row['rule_id']} is {status.lower()} by the document as a whole.",
                row.get("recommendation") or "Review against the playbook rule with legal.",
                "Document-level rule coverage assessment.",
            )

    return findings


# ---------------------------------------------------------------------- #
# Negotiation strategy
# ---------------------------------------------------------------------- #
def _field(text: str, name: str) -> str | None:
    m = re.search(rf"^{name}:\s*(.+)$", text or "", flags=re.MULTILINE)
    return m.group(1).strip() if m else None


def negotiation_strategy(assessment: dict) -> dict | None:
    """Return a strategy for any clause that is not Compliant, else None."""
    if assessment.get("compliance_status") == "Compliant":
        return None

    ids = assessment.get("applicable_rule_ids", [])
    rule = next((e for e in assessment.get("evidence", []) if e.get("rule_id") in ids), None)
    rule_text = rule.get("text", "") if rule else ""

    policy = _field(rule_text, "Policy")
    fallback = _field(rule_text, "Fallback wording") or "Fallback position requires legal approval."
    escalation = _field(rule_text, "Escalation")

    return {
        "clause_id": assessment["clause_id"],
        "rule_id": rule.get("rule_id") if rule else None,
        "preferred_position": policy or "Requires legal review",
        "preferred_wording": assessment.get("suggested_redline"),
        "fallback_position": fallback,
        "escalation_conditions": (
            f"Escalate if the vendor rejects the preferred position or requests an exception. "
            f"Playbook escalation trigger: {escalation}"
            if escalation
            else "Escalate if the vendor rejects the preferred position or requests an exception."
        ),
        "walk_away_conditions": "No automatic walk-away decision; obtain legal approval.",
        "rationale": assessment.get("explanation", ""),
        "requires_legal_review": bool(assessment.get("requires_legal_review", True)),
    }


def build_negotiation_strategies(assessments: list) -> list:
    return [s for s in (negotiation_strategy(a) for a in assessments) if s]