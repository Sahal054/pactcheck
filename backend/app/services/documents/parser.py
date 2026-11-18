from pathlib import Path
import re
import fitz
from docx import Document
from app.schemas.models import Clause

HEADING = re.compile(
    r"(?m)^\s*(?:(?:ARTICLE|SECTION|Clause)\s+)?(\d+(?:\.\d+)*|[IVXLCDM]+)(?:[.)\s:-]+)\s*([^\n]{2,100})\s*$"
)

def extract_text(path: str) -> tuple[str, list[dict]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if p.suffix.lower() == ".pdf":
        doc = fitz.open(path)
        pages = [{"page": i + 1, "text": page.get_text("text")} for i, page in enumerate(doc)]
        return "\n".join(x["text"] for x in pages), pages
    if p.suffix.lower() == ".docx":
        doc = Document(path)
        paragraphs = [par.text for par in doc.paragraphs if par.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)
        text = "\n".join(paragraphs)
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
        blocks = [b.strip() for b in re.split(r"\n\s*\n", full) if len(b.strip()) > 35]
        if len(blocks) > 1:
            return [
                Clause(
                    clause_id=f"CLAUSE_{i+1:03d}",
                    clause_number=str(i + 1),
                    heading=b.splitlines()[0][:70].strip(),
                    text=b,
                    page_start=1,
                    page_end=max(1, len(pages)),
                ).model_dump()
                for i, b in enumerate(blocks)
            ]
        return [
            Clause(
                clause_id="CLAUSE_001",
                clause_number="1",
                heading="Full Document",
                text=full.strip(),
                page_start=1,
                page_end=max(1, len(pages)),
            ).model_dump()
        ]
    clauses = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full)
        # Slice from m.end() so the body does NOT repeat the numbered heading line!
        body = full[m.end():end].strip()
        if not body:
            body = full[m.start():end].strip()
        offset = 0
        start_page = end_page = 1
        for page in pages:
            page_end = offset + len(page["text"]) + 1
            if offset <= m.start() < page_end:
                start_page = page["page"]
            if offset < end <= page_end:
                end_page = page["page"]
            offset = page_end
        clauses.append(
            Clause(
                clause_id=f"CLAUSE_{i+1:03d}",
                clause_number=m.group(1).strip(),
                heading=m.group(2).strip(),
                text=body,
                page_start=start_page,
                page_end=max(start_page, end_page),
            ).model_dump()
        )
    return clauses