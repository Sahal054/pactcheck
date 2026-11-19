from pathlib import Path
import uuid, json
import asyncio
import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.config import settings
from app.schemas.models import ClauseUpdateRequest, SettingsUpdate
from app.services.rag.playbook import index_playbook
from app.services.documents.parser import extract_clauses
from app.services.documents.exporter import compute_word_diff, generate_redlined_docx
from app.services.analysis.reviewer import ContractReviewer
from app.services.analysis.intelligence import (
    cross_clause_findings,
    negotiation_strategy,
)

BASE = Path(settings.data_dir)
for name in ["playbook", "contracts", "indexes", "reports"]:
    (BASE / name).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app):
    await asyncio.to_thread(ensure_default_playbook_indexed)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="PactCheck / ContractIQ API",
    version="2.0.0",
    description="Evidence-backed contract redlining & playbook reviewer",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_default_playbook_indexed():
    faiss_file = BASE / "indexes" / "playbook.faiss"
    default_pb = BASE / "playbook" / "legal_playbook.md"
    if default_pb.exists():
        try:
            if faiss_file.exists():
                from app.services.rag.hybrid import HybridRetriever

                HybridRetriever(str(BASE / "indexes"))
            else:
                index_playbook(str(default_pb), str(BASE / "indexes"))
        except RuntimeError:
            logging.getLogger(__name__).warning(
                "Rebuilding incompatible startup index with the active playbook rules"
            )
            chunks = BASE / "indexes" / "chunks.json"
            if chunks.exists():
                from app.services.rag.hybrid import HybridRetriever

                HybridRetriever(str(BASE / "indexes"), load_existing=False).build(
                    json.loads(chunks.read_text(encoding="utf-8"))
                )
            else:
                index_playbook(str(default_pb), str(BASE / "indexes"))


def validate_document_type(value):
    value = value.upper()
    if value not in {"MSA", "NDA", "DPA", "SOW", "SLA"}:
        raise HTTPException(422, "Unsupported document classification")
    return value


def report_path(review_id):
    if not re.fullmatch(r"[a-f0-9]{32}", review_id):
        raise HTTPException(404, "Report not found")
    return BASE / "reports" / f"{review_id}.json"


def save_report(path, report):
    temporary = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(report, indent=2), encoding="utf-8")
    temporary.replace(path)


def score_contract(assessments, coverage, findings):
    # Fixed weights: clause readiness 60%, mandatory coverage 25%, interaction safety 15%.
    weights = {"Low": 0, "Medium": 0.5, "High": 1, "Unclear": 0.75}
    clause_penalty = sum(weights[a["risk_level"]] for a in assessments) / max(
        1, len(assessments)
    )
    gap_penalty = sum(
        {"Covered": 0, "Partially Covered": 0.5, "Not Covered": 1}.get(r["status"], 1)
        for r in coverage
    ) / max(1, len(coverage))
    interaction_penalty = min(1, sum(weights[f["risk_level"]] for f in findings))
    score = (
        round(
            100
            * (
                1
                - 0.60 * clause_penalty
                - 0.25 * gap_penalty
                - 0.15 * interaction_penalty
            )
        )
        if coverage
        else 0
    )
    high = any(a["risk_level"] == "High" for a in [*assessments, *findings]) or any(
        r["status"] == "Not Covered" for r in coverage
    )
    medium = any(
        a["risk_level"] in {"Medium", "Unclear"} for a in [*assessments, *findings]
    ) or any(r["status"] != "Covered" for r in coverage)
    return max(0, min(100, score)), (
        "High" if high else "Medium" if medium or not coverage else "Low"
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "embedding_provider": settings.embedding_provider,
    }


@app.get("/api/settings")
def get_settings():
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": (
            settings.openrouter_model
            if settings.llm_provider == "openrouter"
            else (
                settings.openai_model
                if settings.llm_provider == "openai"
                else "deterministic-rules-v1"
            )
        ),
        "embedding_provider": settings.embedding_provider,
        "embedding_model": (
            settings.local_embedding_model
            if settings.embedding_provider == "local"
            else (
                settings.openai_embedding_model
                if settings.embedding_provider == "openai"
                else settings.openrouter_embedding_model
            )
        ),
        "api_keys_configured": {
            "openrouter": bool(settings.openrouter_api_key),
            "openai": bool(settings.openai_api_key),
        },
    }


@app.post("/api/settings")
def update_settings(payload: SettingsUpdate):
    if payload.llm_provider:
        settings.llm_provider = payload.llm_provider.lower()
    if payload.llm_model:
        if settings.llm_provider == "openrouter":
            settings.openrouter_model = payload.llm_model
        elif settings.llm_provider == "openai":
            settings.openai_model = payload.llm_model
    if payload.embedding_provider:
        settings.embedding_provider = payload.embedding_provider.lower()
    if payload.openai_api_key is not None and payload.openai_api_key.strip():
        settings.openai_api_key = payload.openai_api_key.strip()
    if payload.openrouter_api_key is not None and payload.openrouter_api_key.strip():
        settings.openrouter_api_key = payload.openrouter_api_key.strip()
    if payload.embedding_model:
        field = {
            "local": "local_embedding_model",
            "openai": "openai_embedding_model",
            "openrouter": "openrouter_embedding_model",
        }[settings.embedding_provider]
        setattr(settings, field, payload.embedding_model.strip())
    from app.services.ai.embeddings import get_embedding_service

    get_embedding_service.cache_clear()
    return {
        **get_settings(),
        "persistence": "Runtime settings; use backend/.env for restart persistence.",
    }


@app.post("/api/settings/test-llm")
def test_llm():
    from app.services.ai.llm import LLMService

    try:
        result = LLMService().complete_json(
            "Return JSON only.", 'Return {"connection":"ok"}.'
        )
        return {"success": True, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e)) from e


@app.post("/api/settings/test-embeddings")
def test_embeddings():
    try:
        from app.services.ai.embeddings import get_embedding_service

        embedder = get_embedding_service()
        vec = embedder.embed(["Contract liability policy test"])
        return {
            "success": True,
            "dimensions": int(vec.shape[1]),
            **embedder.fingerprint(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e)) from e


@app.post("/api/playbook/upload")
async def upload_playbook(file: UploadFile = File(...)):
    suffix = Path(file.filename or "upload").suffix.lower()
    if suffix not in [".md", ".txt", ".pdf", ".docx"]:
        raise HTTPException(400, "Upload PDF, DOCX, Markdown or TXT")
    dest = (
        BASE / "playbook" / f"{uuid.uuid4().hex}_{Path(file.filename or 'upload').name}"
    )
    dest.write_bytes(await file.read())
    return {
        "message": "Playbook uploaded",
        "path": str(dest),
        "filename": file.filename,
    }


@app.post("/api/playbook/index")
def build_index(path: str = Form(...)):
    try:
        rules = index_playbook(path, str(BASE / "indexes"))
        return {"success": True, "indexed_rules": len(rules), "rules": rules}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e)) from e


@app.get("/api/playbook/index-status")
def index_status():
    p = BASE / "indexes" / "playbook.faiss"
    chunks_p = BASE / "indexes" / "chunks.json"
    rule_count = 0
    error = None
    if chunks_p.exists():
        try:
            rule_count = len(json.loads(chunks_p.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            error = "Invalid playbook metadata. Rebuild the index."
    if p.exists() and error is None:
        try:
            from app.services.rag.hybrid import HybridRetriever

            HybridRetriever(str(BASE / "indexes"))
        except (RuntimeError, ValueError, OSError) as exc:
            error = str(exc)
    return {
        "indexed": p.exists() and error is None and rule_count > 0,
        "error": error,
        "index_path": str(p),
        "rule_count": rule_count,
        "playbook_path": str(BASE / "playbook" / "legal_playbook.md"),
    }


@app.get("/api/playbook/rules")
def get_playbook_rules():
    chunks_p = BASE / "indexes" / "chunks.json"
    if not chunks_p.exists():
        return {"rules": []}
    return {"rules": json.loads(chunks_p.read_text(encoding="utf-8"))}


@app.post("/api/contracts/upload")
async def upload_contract(file: UploadFile = File(...)):
    suffix = Path(file.filename or "upload").suffix.lower()
    if suffix not in [".pdf", ".docx", ".md", ".txt"]:
        raise HTTPException(400, "Upload PDF, DOCX, Markdown or TXT")
    dest = (
        BASE
        / "contracts"
        / f"{uuid.uuid4().hex}_{Path(file.filename or 'upload').name}"
    )
    dest.write_bytes(await file.read())
    return {"contract_id": dest.stem, "path": str(dest), "filename": file.filename}


@app.post("/api/review/analyze")
async def analyze_contract(path: str = Form(...), document_type: str = Form("MSA")):
    try:
        document_type = validate_document_type(document_type)
        clauses = await asyncio.to_thread(extract_clauses, path)
        reviewer = ContractReviewer(str(BASE / "indexes"))
        assessments = await reviewer.assess_many_async(clauses, document_type)
        counts = {
            r: sum(1 for a in assessments if a["risk_level"] == r)
            for r in ["High", "Medium", "Low", "Unclear"]
        }
        coverage = reviewer.assess_rule_coverage(clauses, document_type, assessments)
        crosses = cross_clause_findings(
            clauses, assessments, coverage, document_type=document_type
        )
        readiness, overall_risk = score_contract(assessments, coverage, crosses)
        strategies = [
            s
            for s in (
                negotiation_strategy(a)
                for a in assessments
                if a["risk_level"] in ["High", "Medium"]
            )
            if s
        ]
        report = {
            "review_id": uuid.uuid4().hex,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "contract_readiness_score": readiness,
            "overall_risk": overall_risk,
            "rule_coverage": coverage,
            "scoring_version": "1.0",
            "contract_path": path,
            "document_type": document_type,
            "total_clauses": len(clauses),
            "risk_summary": counts,
            "clauses": assessments,
            "cross_clause_findings": crosses,
            "negotiation_strategies": strategies,
            "disclaimer": "AI-assisted preliminary review only. Final decisions require qualified legal review.",
        }
        save_report(report_path(report["review_id"]), report)
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e)) from e


@app.patch("/api/reports/{review_id}/clauses/{clause_id}")
def update_clause_redline(review_id: str, clause_id: str, payload: ClauseUpdateRequest):
    p = report_path(review_id)
    if not p.exists():
        raise HTTPException(404, "Report not found")
    report = json.loads(p.read_text(encoding="utf-8"))
    for c in report.get("clauses", []):
        if c["clause_id"] == clause_id:
            if (
                payload.redline_status == "edited"
                and not (payload.suggested_redline or "").strip()
            ):
                raise HTTPException(422, "Edited redline must contain replacement text")
            if (
                payload.suggested_redline is not None
                and not payload.suggested_redline.strip()
            ):
                raise HTTPException(422, "Replacement text cannot be blank")
            c["redline_status"] = payload.redline_status
            if payload.suggested_redline is not None:
                c["suggested_redline"] = payload.suggested_redline
                c["word_diff"] = compute_word_diff(
                    c["original_text"], payload.suggested_redline
                )
            c["word_diff"] = compute_word_diff(
                c["original_text"],
                (
                    None
                    if payload.redline_status == "rejected"
                    else c.get("suggested_redline")
                ),
            )
            break
    else:
        raise HTTPException(404, "Clause not found")
    save_report(p, report)
    return report


@app.get("/api/reports/{review_id}/export-docx")
def export_report_docx(review_id: str):
    p = report_path(review_id)
    if not p.exists():
        raise HTTPException(404, "Report not found")
    report = json.loads(p.read_text(encoding="utf-8"))
    docx_bytes = generate_redlined_docx(report)
    filename = f"PactCheck_Redlined_{report.get('document_type', 'Contract')}_{review_id[:8]}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/revisions/compare")
async def compare_revisions(
    original_path: str = Form(...),
    revised_path: str = Form(...),
    document_type: str = Form("MSA"),
):
    try:
        document_type = validate_document_type(document_type)
        original, revised = await asyncio.gather(
            asyncio.to_thread(extract_clauses, original_path),
            asyncio.to_thread(extract_clauses, revised_path),
        )
        reviewer = ContractReviewer(str(BASE / "indexes"))
        revised_assessments = {
            a["clause_id"]: a
            for a in await reviewer.assess_many_async(revised, document_type)
        }
        results = []
        matched = set()
        original_headings = {c["heading"].lower() for c in original}
        for old in original:
            candidates = [
                n
                for n in revised
                if n["clause_id"] not in matched
                and n["heading"].lower() == old["heading"].lower()
            ]
            if not candidates:
                candidates = [
                    n
                    for n in revised
                    if n["clause_id"] not in matched
                    and n["heading"].lower() not in original_headings
                    and n.get("clause_number") == old.get("clause_number")
                    and old.get("clause_number")
                ]
            if not candidates:
                results.append(
                    {
                        "original_clause_id": old["clause_id"],
                        "heading": old["heading"],
                        "status": "Removed",
                        "original_text": old["text"],
                        "revised_text": "",
                        "word_diff": compute_word_diff(old["text"], ""),
                        "note": "No matching revised clause found; removal requires legal review",
                    }
                )
                continue
            new = candidates[0]
            matched.add(new["clause_id"])
            changed = old["text"].strip() != new["text"].strip()
            new_assess = revised_assessments.get(new["clause_id"], {})
            results.append(
                {
                    "original_clause_id": old["clause_id"],
                    "revised_clause_id": new["clause_id"],
                    "heading": new["heading"],
                    "status": (
                        "Resolved (Compliant)"
                        if changed
                        and new_assess.get("compliance_status") == "Compliant"
                        else (
                            "Changed - Residual Risk ("
                            + new_assess.get("risk_level", "Unclear")
                            + ")"
                            if changed
                            else "No Material Text Change"
                        )
                    ),
                    "new_risk_level": new_assess.get("risk_level", "Unclear"),
                    "assessment": new_assess,
                    "original_text": old["text"],
                    "revised_text": new["text"],
                    "word_diff": compute_word_diff(old["text"], new["text"]),
                }
            )
        for new in revised:
            if new["clause_id"] not in matched:
                assessment = revised_assessments[new["clause_id"]]
                results.append(
                    {
                        "revised_clause_id": new["clause_id"],
                        "heading": new["heading"],
                        "status": "Added",
                        "new_risk_level": assessment["risk_level"],
                        "original_text": "",
                        "revised_text": new["text"],
                        "word_diff": compute_word_diff("", new["text"]),
                        "assessment": assessment,
                    }
                )
        return {
            "comparisons": results,
            "note": "Semantic re-assessment completed against active Playbook index.",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, str(e)) from e


@app.get("/api/reports/{review_id}")
def get_report(review_id: str):
    p = report_path(review_id)
    if not p.exists():
        raise HTTPException(404, "Report not found")
    return json.loads(p.read_text(encoding="utf-8"))
