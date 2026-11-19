import difflib
import io
import re
from datetime import datetime, timezone
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor


def compute_word_diff(original: str, revised: str | None) -> list[dict]:
    """Return readable diff tokens [{'type': 'equal'|'delete'|'insert', 'text': ...}]."""
    if revised is None or original == revised:
        return [{"type": "equal", "text": original}]
    a_tokens = re.findall(r"\S+\s*|\s+", original)
    b_tokens = re.findall(r"\S+\s*|\s+", revised)
    matcher = difflib.SequenceMatcher(None, a_tokens, b_tokens, autojunk=False)
    if matcher.ratio() < 0.55:
        return ([{"type": "delete", "text": original}] if original else []) + (
            [{"type": "insert", "text": revised}] if revised else []
        )

    ops: list[dict] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            ops.append({"type": "equal", "text": "".join(a_tokens[i1:i2])})
        elif tag == "delete":
            ops.append({"type": "delete", "text": "".join(a_tokens[i1:i2])})
        elif tag == "insert":
            ops.append({"type": "insert", "text": "".join(b_tokens[j1:j2])})
        elif tag == "replace":
            ops.append({"type": "delete", "text": "".join(a_tokens[i1:i2])})
            ops.append({"type": "insert", "text": "".join(b_tokens[j1:j2])})
    return ops


def _add_tracked_change(
    paragraph, text: str, change_type: str, change_id: int, author: str = "PactCheck AI"
):
    """Insert native OOXML <w:ins> or <w:del> revision markup into a python-docx paragraph."""
    tag = "w:ins" if change_type == "insert" else "w:del"
    el = OxmlElement(tag)
    el.set(qn("w:id"), str(change_id))
    el.set(qn("w:author"), author)
    el.set(qn("w:date"), datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    if change_type == "insert":
        color.set(qn("w:val"), "166534")
        rPr.append(color)
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)
    else:
        color.set(qn("w:val"), "991B1B")
        strike = OxmlElement("w:strike")
        rPr.append(strike)
        rPr.append(color)
    r.append(rPr)

    t_tag = "w:t" if change_type == "insert" else "w:delText"
    t = OxmlElement(t_tag)
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    el.append(r)
    paragraph._p.append(el)


def generate_redlined_docx(report: dict) -> bytes:
    """Build a .docx with executive risk scorecard and native Word Track Changes (<w:ins>/<w:del>)."""
    doc = Document()
    doc.core_properties.author = "PactCheck AI"
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(6)
    track = OxmlElement("w:trackRevisions")
    doc.settings.element.append(track)
    doc.add_heading(
        f"PactCheck AI — Redlined {report.get('document_type', 'Contract')}", level=0
    )

    meta = doc.add_paragraph()
    meta_run = meta.add_run(
        f"Review ID: {report.get('review_id', 'N/A')}  |  "
        f"Review timestamp: {report.get('created_at') or datetime.now(timezone.utc).isoformat()}  |  "
        f"Total Clauses: {report.get('total_clauses', 0)}"
    )
    meta_run.font.size = Pt(9.5)
    meta_run.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph(
        f"Contract Readiness Score: {report.get('contract_readiness_score', 0)}/100  |  "
        f"Overall Risk: {report.get('overall_risk', 'Unclear')}"
    )
    summary = report.get("risk_summary", {})
    score_p = doc.add_paragraph()
    score_run = score_p.add_run(
        f"Risk Scorecard:  High: {summary.get('High', 0)}   |   "
        f"Medium: {summary.get('Medium', 0)}   |   "
        f"Low: {summary.get('Low', 0)}   |   "
        f"Unclear: {summary.get('Unclear', 0)}"
    )
    score_run.bold = True

    doc.add_heading("1. Redlined Agreement Text (Native Word Track Changes)", level=1)

    change_id = 1
    for clause in report.get("clauses", []):
        cid = clause.get("clause_id", "")
        heading = clause.get("heading", "")
        risk = clause.get("risk_level", "Unclear")
        status = clause.get("compliance_status", "Not Assessed")
        redline_status = clause.get("redline_status", "pending")
        orig = clause.get("original_text", "")
        redline = clause.get("suggested_redline")

        doc.add_heading(
            f"{clause.get('clause_number') or cid} — {heading} [{risk} Risk · {status}; {redline_status}]",
            level=2,
        )
        body_para = doc.add_paragraph()

        if redline and redline_status != "rejected":
            diffs = compute_word_diff(orig, redline)
            for token in diffs:
                if token["type"] == "equal":
                    body_para.add_run(token["text"])
                elif token["type"] in ("delete", "insert"):
                    _add_tracked_change(
                        body_para, token["text"], token["type"], change_id
                    )
                    change_id += 1
        else:
            body_para.add_run(orig)

        if risk in ("High", "Medium"):
            note_p = doc.add_paragraph()
            rules = ", ".join(clause.get("applicable_rule_ids", [])) or "Manual Review"
            r_label = note_p.add_run(f"[Playbook Grounding: {rules}] ")
            r_label.bold = True
            r_label.font.size = Pt(9)
            r_label.font.color.rgb = RGBColor(30, 69, 105)
            r_exp = note_p.add_run(clause.get("explanation", ""))
            r_exp.font.size = Pt(9)

            if clause.get("counterparty_pushback_email"):
                email_p = doc.add_paragraph()
                e_lbl = email_p.add_run("Vendor Counsel Pushback Email: ")
                e_lbl.bold = True
                e_lbl.font.size = Pt(9)
                from app.services.analysis.reviewer import clean_pushback

                e_txt = email_p.add_run(
                    clean_pushback(clause["counterparty_pushback_email"]) or ""
                )
                e_txt.italic = True
                e_txt.font.size = Pt(9)

    doc.add_heading("2. Missing Playbook Clauses and Coverage Gaps", level=1)
    coverage = report.get("rule_coverage", [])
    if not coverage:
        doc.add_paragraph(
            "No mandatory playbook coverage was available for this document classification. Legal review is required."
        )
    for rule in coverage:
        doc.add_heading(
            f"{rule['rule_id']} — {rule.get('clause_type', '')} [{rule['status']}]",
            level=2,
        )
        doc.add_paragraph(rule.get("explanation", ""))
        if rule.get("clause_ids"):
            doc.add_paragraph("Related clauses: " + ", ".join(rule["clause_ids"]))
        if rule["status"] != "Covered" and rule.get("preferred_wording"):
            doc.add_paragraph(
                "Playbook preferred position: " + rule["preferred_wording"]
            )

    doc.add_heading("3. Cross-Clause Risk Intelligence", level=1)
    findings = report.get("cross_clause_findings", [])
    if not findings:
        doc.add_paragraph(
            "No interactions detected by the configured cross-clause checks."
        )
    for finding in findings:
        doc.add_heading(
            f"{finding['finding_id']} — {finding['relationship']} [{finding['risk_level']}]",
            level=2,
        )
        doc.add_paragraph(
            "Related clauses: " + ", ".join(finding.get("related_clause_ids", []))
        )
        doc.add_paragraph(finding.get("explanation", ""))
        doc.add_paragraph("Recommendation: " + finding.get("recommendation", ""))
    doc.add_paragraph(
        report.get(
            "disclaimer",
            "AI-assisted review. Final decisions require qualified legal review.",
        )
    )
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
