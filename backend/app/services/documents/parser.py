"""Extract ordered document text and segment numbered or Markdown headings."""

from bisect import bisect_right
from pathlib import Path
import re
import pymupdf as fitz
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from app.schemas.models import Clause

HEADING = re.compile(
    r"(?m)^[ \t]*(?:#{1,6}[ \t]+)?(?:(?:ARTICLE|SECTION|Clause)[ \t]+)?"
    r"(\d+(?:\.\d+)*|[IVXLCDM]+)[.) \t:-]+([^\n\r]{2,100})[ \t]*$"
    r"|^[ \t]*#{1,6}[ \t]+([^\n\r]+)$",
    re.IGNORECASE,
)


def extract_text(path: str) -> tuple[str, list[dict]]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        with fitz.open(path) as doc:
            pages = [
                {"page": i + 1, "text": page.get_text("text")}
                for i, page in enumerate(doc)
            ]
    elif suffix == ".docx":
        doc = Document(path)
        page_texts = [""]
        # Walk body children so table clauses remain between their surrounding paragraphs.
        for child in doc.element.body:
            if child.tag == qn("w:p"):
                paragraphs = [Paragraph(child, doc)]
            elif child.tag == qn("w:tbl"):
                table = Table(child, doc)
                paragraphs = []
                seen_cells = set()
                for row in table.rows:
                    for cell in row.cells:
                        if cell._tc not in seen_cells:
                            seen_cells.add(cell._tc)
                            paragraphs.extend(cell.paragraphs)
            else:
                continue
            for par in paragraphs:
                is_heading = par.style is not None and par.style.name.startswith(
                    "Heading"
                )
                if is_heading and not HEADING.match(par.text):
                    page_texts[-1] += f"## {par.text}\n"
                else:
                    # Explicit and rendered Word page breaks are the only reliable page markers without layout.
                    for node in par._p.iter():
                        if node.tag == qn("w:t"):
                            page_texts[-1] += node.text or ""
                        elif node.tag == qn("w:tab"):
                            page_texts[-1] += "\t"
                        elif node.tag == qn("w:lastRenderedPageBreak") or (
                            node.tag == qn("w:br") and node.get(qn("w:type")) == "page"
                        ):
                            page_texts.append("")
                        elif node.tag == qn("w:br"):
                            page_texts[-1] += "\n"
                    page_texts[-1] += "\n"
        pages = [{"page": i + 1, "text": text} for i, text in enumerate(page_texts)]
    elif suffix in (".md", ".txt"):
        pages = [
            {"page": 1, "text": p.read_text(encoding="utf-8-sig").replace("\r\n", "\n")}
        ]
    else:
        raise ValueError("Supported files: PDF, DOCX, Markdown and TXT")
    return "\n".join(page["text"] for page in pages), pages


def extract_clauses(path: str) -> list[dict]:
    full, pages = extract_text(path)
    if not full.strip():
        raise ValueError(
            "No readable text extracted. Scanned PDFs need OCR before review."
        )
    page_offsets, offset = [], 0
    for page in pages:
        page_offsets.append(offset)
        offset += len(page["text"]) + 1

    def page_at(position):
        return max(1, bisect_right(page_offsets, position))

    matches = list(HEADING.finditer(full))
    clauses = []
    if matches:
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(full)
            body = full[match.end() : end].strip()
            last_char = max(match.start(), len(full[:end].rstrip()) - 1)
            clauses.append(
                Clause(
                    clause_id=f"CLAUSE_{i + 1:03d}",
                    clause_number=match.group(1),
                    heading=(match.group(2) or match.group(3)).strip().strip("#* "),
                    text=body,
                    page_start=page_at(match.start()),
                    page_end=page_at(last_char),
                ).model_dump()
            )
    else:
        blocks = list(re.finditer(r"\S[\s\S]*?(?=\n[ \t]*\n|\Z)", full))
        for i, block in enumerate(blocks):
            clauses.append(
                Clause(
                    clause_id=f"CLAUSE_{i + 1:03d}",
                    heading=(
                        "Full Document" if len(blocks) == 1 else f"Provision {i + 1}"
                    ),
                    text=block.group().strip(),
                    page_start=page_at(block.start()),
                    page_end=page_at(block.end() - 1),
                ).model_dump()
            )
    return clauses
