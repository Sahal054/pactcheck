from pathlib import Path
import uuid, json
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.config import settings
from app.schemas.models import ClauseUpdateRequest, SettingsUpdate
from app.services.rag.playbook import index_playbook
from app.services.documents.parser import extract_clauses
from app.services.documents.exporter import compute_word_diff, generate_redlined_docx
from app.services.analysis.reviewer import ContractReviewer
from app.services.analysis.intelligence import cross_clause_findings, negotiation_strategy

BASE = Path(settings.data_dir)
for name in ["playbook", "contracts", "indexes", "reports"]:
    (BASE / name).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PactCheck / ContractIQ API", version="2.0.0", description="Evidence-backed contract redlining & playbook reviewer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def ensure_default_playbook_indexed():
    faiss_file = BASE / "indexes" / "playbook.faiss"
    default_pb = BASE / "playbook" / "legal_playbook.md"
    if not faiss_file.exists() and default_pb.exists():
        try:
            index_playbook(str(default_pb), str(BASE / "indexes"))
        except Exception:
            pass


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_provider": settings.llm_provider, "embedding_provider": settings.embedding_provider}


@app.get("/api/settings")
def get_settings():
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.openrouter_model if settings.llm_provider == "openrouter" else settings.openai_model,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": (
            settings.local_embedding_model
            if settings.embedding_provider == "local"
            else settings.openai_embedding_model
            if settings.embedding_provider == "openai"
            else settings.openrouter_embedding_model
        ),
        "api_keys_configured": {"openrouter": bool(settings.openrouter_api_key), "openai": bool(settings.openai_api_key)},
    }


@app.post("/api/settings")
def update_settings(payload: SettingsUpdate):
    if payload.llm_provider:
        settings.llm_provider = payload.llm_provider.lower()
    if payload.llm_model:
        if settings.llm_provider == "openrouter":
            settings.openrouter_model = payload.llm_model
        else:
            settings.openai_model = payload.llm_model
    if payload.embedding_provider:
        settings.embedding_provider = payload.embedding_provider.lower()
    if payload.openai_api_key is not None and payload.openai_api_key.strip():
        settings.openai_api_key = payload.openai_api_key.strip()
    if payload.openrouter_api_key is not None and payload.openrouter_api_key.strip():
        settings.openrouter_api_key = payload.openrouter_api_key.strip()
    return get_settings()


@app.post("/api/settings/test-llm")
def test_llm():
    from app.services.ai.llm import LLMService
    try:
        result = LLMService().complete_json("Return JSON only.", 'Return {"connection":"ok"}.')
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/settings/test-embeddings")
def test_embeddings():
    try:
        from app.services.ai.embeddings import EmbeddingService
        vec = EmbeddingService().embed(["Contract liability policy test"])
        return {"success": True, "dimensions": int(vec.shape[1]), "provider": settings.embedding_provider}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/api/playbook/upload")
async def upload_playbook(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".md", ".txt", ".pdf"]:
        raise HTTPException(400, "Upload PDF, Markdown or TXT")
    dest = BASE / "playbook" / f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest.write_bytes(await file.read())
    return {"message": "Playbook uploaded", "path": str(dest), "filename": file.filename}


@app.post("/api/playbook/index")
def build_index(path: str = Form(...)):
    try:
        rules = index_playbook(path, str(BASE / "indexes"))
        return {"success": True, "indexed_rules": len(rules), "rules": rules}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/api/playbook/index-status")
def index_status():
    p = BASE / "indexes" / "playbook.faiss"
    chunks_p = BASE / "indexes" / "chunks.json"
    rule_count = 0
    if chunks_p.exists():
        try:
            rule_count = len(json.loads(chunks_p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return {"indexed": p.exists(), "index_path": str(p), "rule_count": rule_count, "playbook_path": str(BASE / "playbook" / "legal_playbook.md")}


@app.get("/api/playbook/rules")
def get_playbook_rules():
    chunks_p = BASE / "indexes" / "chunks.json"
    if not chunks_p.exists():
        return {"rules": []}
    return {"rules": json.loads(chunks_p.read_text(encoding="utf-8"))}


@app.post("/api/contracts/upload")
async def upload_contract(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".pdf", ".docx", ".md", ".txt"]:
        raise HTTPException(400, "Upload PDF, DOCX, Markdown or TXT")
    dest = BASE / "contracts" / f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest.write_bytes(await file.read())
    return {"contract_id": dest.stem, "path": str(dest), "filename": file.filename}


@app.post("/api/review/analyze")
async def analyze_contract(path: str = Form(...), document_type: str = Form("MSA")):
    try:
        clauses = extract_clauses(path)
        reviewer = ContractReviewer(str(BASE / "indexes"))
        assessments = await reviewer.assess_many_async(clauses, document_type)
        counts = {r: sum(1 for a in assessments if a["risk_level"] == r) for r in ["High", "Medium", "Low", "Unclear"]}
        crosses = cross_clause_findings(clauses, assessments, document_type=document_type)
        strategies = [s for s in (negotiation_strategy(a) for a in assessments if a["risk_level"] in ["High", "Medium"]) if s]
        report = {
            "review_id": uuid.uuid4().hex,
            "contract_path": path,
            "document_type": document_type,
            "total_clauses": len(clauses),
            "risk_summary": counts,
            "clauses": assessments,
            "cross_clause_findings": crosses,
            "negotiation_strategies": strategies,
            "disclaimer": "AI-assisted preliminary review only. Final decisions require qualified legal review.",
        }
        (BASE / "reports" / f"{report['review_id']}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    except Exception as e:
        raise HTTPException(400, str(e))


@app.patch("/api/reports/{review_id}/clauses/{clause_id}")
def update_clause_redline(review_id: str, clause_id: str, payload: ClauseUpdateRequest):
    p = BASE / "reports" / f"{review_id}.json"
    if not p.exists():
        raise HTTPException(404, "Report not found")
    report = json.loads(p.read_text(encoding="utf-8"))
    for c in report.get("clauses", []):
        if c["clause_id"] == clause_id:
            c["redline_status"] = payload.redline_status
            if payload.suggested_redline is not None:
                c["suggested_redline"] = payload.suggested_redline
                c["word_diff"] = compute_word_diff(c["original_text"], payload.suggested_redline)
            break
    p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


@app.get("/api/reports/{review_id}/export-docx")
def export_report_docx(review_id: str):
    p = BASE / "reports" / f"{review_id}.json"
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
async def compare_revisions(original_path: str = Form(...), revised_path: str = Form(...), document_type: str = Form("MSA")):
    try:
        original = extract_clauses(original_path)
        revised = extract_clauses(revised_path)
        reviewer = ContractReviewer(str(BASE / "indexes"))
        revised_assessments = {a["clause_id"]: a for a in await reviewer.assess_many_async(revised, document_type)}
        results = []
        for old in original:
            candidates = [n for n in revised if n.get("clause_number") == old.get("clause_number") and old.get("clause_number")]
            if not candidates:
                candidates = [n for n in revised if n["heading"].lower() == old["heading"].lower()]
            if not candidates:
                results.append({"original_clause_id": old["clause_id"], "heading": old["heading"], "status": "Removed / Unresolved", "note": "No matching revised clause found"})
                continue
            new = candidates[0]
            changed = old["text"].strip() != new["text"].strip()
            new_assess = revised_assessments.get(new["clause_id"], {})
            results.append({
                "original_clause_id": old["clause_id"],
                "revised_clause_id": new["clause_id"],
                "heading": new["heading"],
                "status": (
                    "Resolved (Compliant)"
                    if changed and new_assess.get("compliance_status") == "Compliant"
                    else "Changed - Residual Risk (" + new_assess.get("risk_level", "Unclear") + ")"
                    if changed
                    else "No Material Text Change"
                ),
                "new_risk_level": new_assess.get("risk_level", "Unclear"),
                "original_text": old["text"],
                "revised_text": new["text"],
                "word_diff": compute_word_diff(old["text"], new["text"]),
            })
        return {"comparisons": results, "note": "Semantic re-assessment completed against active Playbook index."}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/api/reports/{review_id}")
def get_report(review_id: str):
    p = BASE / "reports" / f"{review_id}.json"
    if not p.exists():
        raise HTTPException(404, "Report not found")
    return json.loads(p.read_text(encoding="utf-8"))