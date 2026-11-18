from pathlib import Path
import shutil, uuid, json
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.services.rag.playbook import index_playbook, parse_playbook
from app.services.rag.hybrid import HybridRetriever
from app.services.documents.parser import extract_clauses
from app.services.analysis.reviewer import ContractReviewer
from app.services.analysis.intelligence import cross_clause_findings, negotiation_strategy

BASE = Path(settings.data_dir)
for name in ["playbook", "contracts", "indexes", "reports"]:
    (BASE / name).mkdir(parents=True, exist_ok=True)
app = FastAPI(title="ContractIQ API", version="1.0.0", description="Evidence-backed contract intelligence prototype")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok", "llm_provider": settings.llm_provider, "embedding_provider": settings.embedding_provider}

@app.get("/api/settings")
def get_settings():
    return {"llm_provider": settings.llm_provider, "llm_model": settings.openrouter_model if settings.llm_provider == "openrouter" else settings.openai_model, "embedding_provider": settings.embedding_provider, "embedding_model": settings.local_embedding_model if settings.embedding_provider == "local" else settings.openai_embedding_model if settings.embedding_provider == "openai" else settings.openrouter_embedding_model, "api_keys_configured": {"openrouter": bool(settings.openrouter_api_key), "openai": bool(settings.openai_api_key)}}

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
    if suffix not in [".md", ".txt", ".pdf"]: raise HTTPException(400, "Upload PDF, Markdown or TXT")
    dest = BASE / "playbook" / f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest.write_bytes(await file.read())
    return {"message": "Playbook uploaded", "path": str(dest), "filename": file.filename}

@app.post("/api/playbook/index")
def build_index(path: str = Form(...)):
    try:
        rules = index_playbook(path, str(BASE / "indexes"))
        return {"success": True, "indexed_rules": len(rules), "rules": rules}
    except Exception as e: raise HTTPException(400, str(e))

@app.get("/api/playbook/index-status")
def index_status():
    p = BASE / "indexes" / "playbook.faiss"
    return {"indexed": p.exists(), "index_path": str(p)}

@app.post("/api/contracts/upload")
async def upload_contract(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".pdf", ".docx", ".md", ".txt"]: raise HTTPException(400, "Upload PDF, DOCX, Markdown or TXT")
    dest = BASE / "contracts" / f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest.write_bytes(await file.read())
    return {"contract_id": dest.stem, "path": str(dest), "filename": file.filename}

@app.post("/api/review/analyze")
def analyze_contract(path: str = Form(...), document_type: str = Form("MSA")):
    try:
        clauses = extract_clauses(path)
        reviewer = ContractReviewer(str(BASE / "indexes"))
        assessments = [reviewer.assess(c, document_type) for c in clauses]
        counts = {r: sum(1 for a in assessments if a["risk_level"] == r) for r in ["High", "Medium", "Low", "Unclear"]}
        crosses = cross_clause_findings(clauses, assessments)
        strategies = [negotiation_strategy(a) for a in assessments if a["risk_level"] in ["High", "Medium"]]
        report = {"review_id": uuid.uuid4().hex, "document_type": document_type, "total_clauses": len(clauses), "risk_summary": counts, "clauses": assessments, "cross_clause_findings": crosses, "negotiation_strategies": strategies, "disclaimer": "AI-assisted preliminary review only. Final decisions require qualified legal review."}
        (BASE / "reports" / f"{report['review_id']}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    except Exception as e: raise HTTPException(400, str(e))

@app.post("/api/revisions/compare")
def compare_revisions(original_path: str = Form(...), revised_path: str = Form(...)):
    try:
        original = extract_clauses(original_path); revised = extract_clauses(revised_path)
        results = []
        for old in original:
            candidates = [n for n in revised if n.get("clause_number") == old.get("clause_number") and old.get("clause_number")]
            if not candidates: candidates = [n for n in revised if n["heading"].lower() == old["heading"].lower()]
            if not candidates:
                results.append({"original_clause_id": old["clause_id"], "status": "Unresolved", "note": "No matching revised clause found"}); continue
            new = candidates[0]
            changed = old["text"].strip() != new["text"].strip()
            results.append({"original_clause_id": old["clause_id"], "revised_clause_id": new["clause_id"], "status": "Changed - Re-review required" if changed else "No Material Text Change", "original_text": old["text"], "revised_text": new["text"]})
        return {"comparisons": results, "note": "Text/version comparison is preliminary; semantic resolution must be confirmed by re-running policy assessment."}
    except Exception as e: raise HTTPException(400, str(e))

@app.get("/api/reports/{review_id}")
def get_report(review_id: str):
    p = BASE / "reports" / f"{review_id}.json"
    if not p.exists(): raise HTTPException(404, "Report not found")
    return json.loads(p.read_text())
