from pathlib import Path
import re
import fitz
from docx import Document
from app.schemas.models import Clause

HEADING = re.compile(r"(?m)^\s*(\d+(?:\.\d+)*)(?:[.)])?\s+([^\n]{2,100})\s*$")

def extract_text(path: str) -> tuple[str, list[dict]]:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        doc = fitz.open(path)
        pages = [{"page": i + 1, "text": page.get_text("text")} for i, page in enumerate(doc)]
        return "\n".join(x["text"] for x in pages), pages
    if p.suffix.lower() == ".docx":
        doc = Document(path)
        text = "\n".join(par.text for par in doc.paragraphs)
        return text, [{"page": 1, "text": text}]
    if p.suffix.lower() in (".md", ".txt"):
        text = p.read_text(encoding="utf-8")
        return text, [{"page": 1, "text": text}]
    raise ValueError("Supported files: PDF, DOCX, Markdown and TXT")

def extract_clauses(path: str) -> list[dict]:
    full, pages = extract_text(path)
    if not full.strip():
        raise ValueError("No readable text extracted. Scanned PDFs need OCR before review.")
    matches = list(HEADING.finditer(full))
    if not matches:
        return [Clause(clause_id="CLAUSE_001", heading="Full document", text=full, page_start=1, page_end=max(1, len(pages))).model_dump()]
    clauses = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full)
        body = full[m.start():end].strip()
        start_page = 1 + sum(len(p["text"]) for p in pages if sum(len(x["text"]) for x in pages[:pages.index(p)]) < m.start())
        # Map character offset to page without assuming page boundaries are clause boundaries.
        offset = 0
        start_page = end_page = 1
        for page in pages:
            page_end = offset + len(page["text"])
            if offset <= m.start() < page_end: start_page = page["page"]
            if offset < end <= page_end: end_page = page["page"]
            offset = page_end
        clauses.append(Clause(clause_id=f"CLAUSE_{i+1:03d}", clause_number=m.group(1), heading=m.group(2).strip(), text=body, page_start=start_page, page_end=max(start_page, end_page)).model_dump())
    return clauses
