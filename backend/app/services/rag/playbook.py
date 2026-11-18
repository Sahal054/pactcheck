import re
from pathlib import Path
from app.services.rag.hybrid import HybridRetriever

RULE_RE = re.compile(r"(?m)^##\s+(RULE_\d+)\s*[-–:]\s*(.+)$")

def parse_playbook(text: str, source: str = "playbook.md") -> list[dict]:
    matches = list(RULE_RE.finditer(text))
    rules = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.end():end].strip()
        def section(name):
            pat = re.search(rf"(?ims)^\s*{re.escape(name)}\s*:\s*(.*?)(?=^\s*[A-Za-z /_-]+\s*:\s*|\Z)", block)
            return pat.group(1).strip() if pat else ""
        rules.append({
            "rule_id": m.group(1), "clause_type": m.group(2).strip().lower(),
            "text": f"{m.group(1)} - {m.group(2)}\n{block}",
            "policy": section("Policy"), "red_flags": [x.strip(" -*") for x in section("Red flags").splitlines() if x.strip()],
            "preferred_wording": section("Preferred wording"), "fallback_wording": section("Fallback wording") or None,
            "applicable_documents": [x.strip() for x in (section("Applicable documents") or "NDA, MSA").replace("and", ",").split(",")],
            "escalation_conditions": [x.strip(" -*") for x in section("Escalation").splitlines() if x.strip()],
            "source": source
        })
    return rules

def index_playbook(path: str, index_dir: str = "./data/indexes"):
    text = Path(path).read_text(encoding="utf-8") if Path(path).suffix.lower() in (".md", ".txt") else None
    if text is None:
        from app.services.documents.parser import extract_text
        text, _ = extract_text(path)
    rules = parse_playbook(text, Path(path).name)
    if not rules:
        # Safe fallback: index headings/paragraphs as evidence chunks, but warn user.
        chunks = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 40]
        rules = [{"rule_id": f"UNSTRUCTURED_{i+1:03d}", "clause_type": "general", "text": c, "policy": c, "source": Path(path).name} for i, c in enumerate(chunks)]
    retriever = HybridRetriever(index_dir)
    retriever.build(rules)
    return rules
