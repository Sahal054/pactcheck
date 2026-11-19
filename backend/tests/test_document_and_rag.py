import io
import json
import sys
import types
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import numpy as np
import pytest
import pymupdf as fitz
from docx import Document
from docx.enum.text import WD_BREAK
from app.config import settings
from app.services.documents.parser import extract_clauses
from app.services.documents.exporter import compute_word_diff, generate_redlined_docx
from app.services.ai.embeddings import (
    EmbeddingService,
    HASH_MODEL,
    get_embedding_service,
)
from app.services.rag.hybrid import HybridRetriever
from app.services.rag.playbook import index_playbook
from conftest import ORIGINAL_LOCAL_MODEL, PLAYBOOK


@pytest.mark.parametrize("suffix,prefix", [(".txt", ""), (".md", "## ")])
def test_text_and_markdown_segmentation(tmp_path, suffix, prefix):
    path = tmp_path / ("contract" + suffix)
    path.write_text(
        f"Test Agreement\n\n{prefix}1. Scope of Services\nVendor shall provide support.\n\n{prefix}1.1 Service Levels\nUptime shall be 99 percent.\n\n{prefix}2.1 Payment\nPayment is due in thirty days."
    )
    clauses = extract_clauses(str(path))
    assert [c["clause_number"] for c in clauses] == ["1", "1.1", "2.1"]
    assert clauses[0]["text"] == "Vendor shall provide support."
    assert clauses[1]["heading"] == "Service Levels"
    assert all(
        f"{c['clause_number']}. {c['heading']}" not in c["text"] for c in clauses
    )
    assert all(c["page_start"] == c["page_end"] == 1 for c in clauses)


def test_markdown_unnumbered_headings_and_empty_clause(tmp_path):
    path = tmp_path / "c.md"
    path.write_text(
        "## Scope\nServices are provided.\n## Termination\n## Governing Law\nApproval is required."
    )
    clauses = extract_clauses(str(path))
    assert [c["heading"] for c in clauses] == ["Scope", "Termination", "Governing Law"]
    assert clauses[1]["text"] == ""


def test_docx_tables_order_multilevel_headings_and_pages(tmp_path):
    path = tmp_path / "c.docx"
    doc = Document()
    doc.add_heading("1.1 Scope of Services", level=1)
    doc.add_paragraph("Services must meet the specifications.")
    table = doc.add_table(rows=2, cols=1)
    table.cell(0, 0).text = "2.1 Payment"
    table.cell(1, 0).text = "Invoices are payable within thirty days."
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    doc.add_heading("3. Confidentiality", level=1)
    doc.add_paragraph("Each party shall protect confidential information.")
    doc.save(path)
    clauses = extract_clauses(str(path))
    assert [c["clause_number"] for c in clauses] == ["1.1", "2.1", "3"]
    assert clauses[1]["text"] == "Invoices are payable within thirty days."
    assert clauses[0]["page_start"] == clauses[0]["page_end"] == 1
    assert clauses[2]["page_start"] == clauses[2]["page_end"] == 2
    assert all(c["heading"] not in c["text"] for c in clauses)


def test_pdf_body_continuation_and_page_tracking(tmp_path):
    path = tmp_path / "c.pdf"
    doc = fitz.open()
    doc.new_page().insert_text(
        (72, 72), "1. Scope of Services\nServices begin immediately."
    )
    doc.new_page().insert_text(
        (72, 72),
        "Support continues on this page.\n2.1 Payment\nInvoices are due in thirty days.",
    )
    doc.save(path)
    doc.close()
    clauses = extract_clauses(str(path))
    assert len(clauses) == 2
    assert clauses[0]["page_start"] == 1 and clauses[0]["page_end"] == 2
    assert clauses[1]["page_start"] == clauses[1]["page_end"] == 2
    assert "Scope of Services" not in clauses[0]["text"]
    assert "continues on this page" in clauses[0]["text"]


def test_empty_and_unsupported_document(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("  ")
    with pytest.raises(ValueError, match="No readable text"):
        extract_clauses(str(empty))
    unsupported = tmp_path / "bad.csv"
    unsupported.write_text("text")
    with pytest.raises(ValueError, match="Supported"):
        extract_clauses(str(unsupported))


@pytest.mark.parametrize(
    "query,expected",
    [
        (
            "limitation of liability aggregate liability cap twelve months fees",
            "RULE_001",
        ),
        (
            "intellectual property ownership bespoke deliverables vest ABC upon payment",
            "RULE_002",
        ),
    ],
)
def test_hybrid_dense_bm25_rrf_ranking(index_dir, query, expected):
    retriever = HybridRetriever(str(index_dir))
    assert retriever.index.ntotal == 6 and retriever.bm25 is not None
    hits = retriever.search(query, top_k=3)
    assert hits[0]["rule_id"] == expected
    assert len(hits) == 3 and all(h["retrieval_score"] > 0 for h in hits)


def test_retrieval_filters_before_top_k(index_dir):
    hits = HybridRetriever(str(index_dir)).search(
        "liability intellectual property termination", top_k=3, document_type="NDA"
    )
    assert {h["rule_id"] for h in hits} == {"RULE_001", "RULE_003", "RULE_006"}
    assert all("NDA" in h["applicable_documents"] for h in hits)
    assert (
        HybridRetriever(str(index_dir)).search("liability", document_type="DPA") == []
    )


def test_fingerprint_mismatch_and_explicit_reindex(index_dir):
    config = index_dir / "embedding_config.json"
    metadata = json.loads(config.read_text())
    metadata["model"] = "incompatible-model"
    config.write_text(json.dumps(metadata))
    with pytest.raises(RuntimeError, match="mismatch"):
        HybridRetriever(str(index_dir))
    assert len(index_playbook(str(PLAYBOOK), str(index_dir))) == 6
    assert (
        HybridRetriever(str(index_dir)).search("liability")[0]["rule_id"] == "RULE_001"
    )


def test_dimension_mismatch_is_rejected(index_dir):
    config = index_dir / "embedding_config.json"
    metadata = json.loads(config.read_text())
    metadata["dimensions"] = 12
    config.write_text(json.dumps(metadata))
    with pytest.raises(RuntimeError, match="metadata"):
        HybridRetriever(str(index_dir))


def test_offline_hub_falls_back_to_deterministic_signed_hashing(monkeypatch):
    def unavailable(*args, **kwargs):
        raise OSError("HuggingFace Hub is offline")

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        types.SimpleNamespace(SentenceTransformer=unavailable),
    )
    monkeypatch.setattr(EmbeddingService, "_local_model", ORIGINAL_LOCAL_MODEL)
    embedder = EmbeddingService()
    a = embedder.embed(["liability cap liability", "ownership of deliverables", ""])
    b = EmbeddingService().embed(
        ["liability cap liability", "ownership of deliverables", ""]
    )
    assert a.shape == (3, 384) and a.dtype == np.float32
    np.testing.assert_array_equal(a, b)
    np.testing.assert_allclose(np.linalg.norm(a[:2], axis=1), 1, rtol=1e-6)
    assert (a > 0).any() and (a < 0).any()
    assert embedder.fingerprint()["model"] == HASH_MODEL
    assert np.isfinite(a).all()
    assert embedder.embed([]).shape == (0, 384)


def test_cached_minilm_remains_primary(monkeypatch):
    class MiniLM:
        def __init__(self, name, **kwargs):
            assert name == settings.local_embedding_model and kwargs["local_files_only"]

        def encode(self, texts, **kwargs):
            return np.ones((len(texts), 384), dtype="float32") / np.sqrt(384)

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        types.SimpleNamespace(SentenceTransformer=MiniLM),
    )
    monkeypatch.setattr(EmbeddingService, "_local_model", ORIGINAL_LOCAL_MODEL)
    embedder = EmbeddingService()
    assert embedder.embed(["hello"]).shape == (1, 384)
    assert embedder.fingerprint()["model"] == settings.local_embedding_model


@pytest.mark.parametrize(
    "original,revised",
    [
        (
            "Vendor has unlimited liability.",
            "Each party is responsible up to annual fees.",
        ),
        ("Fees are payable in thirty days.", "Fees are payable in sixty days."),
        ("Old clause", ""),
        ("", "New clause"),
        ("1. Meaning\nBody remains intact.", "1. Meaning\nBody has changed."),
    ],
)
def test_word_diff_roundtrips_and_full_rewrites(original, revised):
    diff = compute_word_diff(original, revised)
    assert "".join(t["text"] for t in diff if t["type"] != "insert") == original
    assert "".join(t["text"] for t in diff if t["type"] != "delete") == revised
    if original.startswith("Vendor"):
        assert [t["type"] for t in diff] == ["delete", "insert"]


def export_fixture(status):
    return {
        "review_id": "a" * 32,
        "created_at": "2026-11-19T12:00:00+00:00",
        "document_type": "MSA",
        "total_clauses": 1,
        "contract_readiness_score": 40,
        "overall_risk": "High",
        "risk_summary": {"High": 1},
        "clauses": [
            {
                "clause_id": "C1",
                "heading": "Liability",
                "original_text": "Vendor has unlimited liability.",
                "suggested_redline": "Each party is responsible up to annual fees.",
                "redline_status": status,
                "risk_level": "High",
                "compliance_status": "Non-Compliant",
                "applicable_rule_ids": ["RULE_001"],
                "explanation": "Cap liability.",
                "counterparty_pushback_email": "Subject: Liability\nDear Counsel,\nPlease agree to a bounded cap. We appreciate your consideration.",
            }
        ],
        "rule_coverage": [
            {
                "rule_id": "RULE_004",
                "clause_type": "termination",
                "status": "Not Covered",
                "explanation": "Missing termination.",
            }
        ],
        "cross_clause_findings": [
            {
                "finding_id": "CROSS_001",
                "relationship": "Cap exclusion",
                "risk_level": "High",
                "explanation": "Indemnity overrides cap.",
                "recommendation": "Agree a cap.",
            }
        ],
    }


@pytest.mark.parametrize("status", ["pending", "accepted", "edited", "rejected"])
def test_docx_track_changes_and_full_report(status):
    blob = generate_redlined_docx(export_fixture(status))
    with ZipFile(io.BytesIO(blob)) as archive:
        assert archive.testzip() is None
        assert "[Content_Types].xml" in archive.namelist()
        xml = archive.read("word/document.xml")
        root = ET.fromstring(xml)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        ins = root.findall(".//w:ins", ns)
        deletions = root.findall(".//w:del", ns)
        if status == "rejected":
            assert not ins and not deletions
            assert b"Vendor has unlimited liability." in xml
        else:
            assert ins and deletions
            for el in ins + deletions:
                assert el.attrib["{" + ns["w"] + "}author"] == "PactCheck AI"
            assert root.findall(".//w:ins//w:u", ns) and root.findall(
                ".//w:del//w:strike", ns
            )
        for value in (
            b"Review ID",
            b"Contract Readiness Score: 40",
            b"Risk Scorecard",
            b"Coverage Gaps",
            b"Cross-Clause Risk Intelligence",
            b"RULE_004",
            b"CROSS_001",
            b"Playbook Grounding",
        ):
            assert value in xml
        assert b"Subject:" not in xml and b"Dear Counsel" not in xml
    assert len(Document(io.BytesIO(blob)).paragraphs) > 10
