import io
import json
from zipfile import ZipFile
import pytest
from app import main
from app.services.rag.hybrid import HybridRetriever
from conftest import SAMPLES, PLAYBOOK


def upload(client, filename="Sample_High_Risk_MSA.txt"):
    response = client.post(
        "/api/contracts/upload",
        files={"file": (filename, (SAMPLES / filename).read_bytes(), "text/plain")},
    )
    assert response.status_code == 200
    return response.json()["path"]


def review(client):
    path = upload(client)
    response = client.post(
        "/api/review/analyze", data={"path": path, "document_type": "MSA"}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_startup_auto_indexes_and_health(client):
    assert (main.BASE / "indexes/playbook.faiss").is_file()
    assert client.get("/api/health").json() == {
        "status": "ok",
        "llm_provider": "mock",
        "embedding_provider": "local",
    }
    status = client.get("/api/playbook/index-status").json()
    assert status["indexed"] and status["rule_count"] == 6
    assert len(client.get("/api/playbook/rules").json()["rules"]) == 6


def test_playbook_upload_explicit_index_and_rules(client):
    response = client.post(
        "/api/playbook/upload",
        files={"file": ("policy.md", PLAYBOOK.read_bytes(), "text/markdown")},
    )
    assert response.status_code == 200
    response = client.post(
        "/api/playbook/index", data={"path": response.json()["path"]}
    )
    assert response.status_code == 200 and response.json()["indexed_rules"] == 6
    rules = client.get("/api/playbook/rules").json()["rules"]
    assert rules[0]["rule_id"] == "RULE_001"
    assert rules[1]["applicable_documents"] == ["MSA"]


def test_complete_review_patch_and_export_workflow(client):
    report = review(client)
    assert report["total_clauses"] == 7 and report["risk_summary"] == {
        "High": 5,
        "Medium": 0,
        "Low": 2,
        "Unclear": 0,
    }
    assert (
        report["overall_risk"] == "High"
        and 0 <= report["contract_readiness_score"] <= 100
    )
    assert report["created_at"]
    assert any(
        r["rule_id"] == "RULE_004" and r["status"] == "Not Covered"
        for r in report["rule_coverage"]
    )
    rid = report["review_id"]
    cid = report["clauses"][2]["clause_id"]
    assert client.get("/api/reports/" + rid).json() == report
    for state in ("accepted", "edited", "rejected"):
        payload = {"redline_status": state}
        if state == "edited":
            payload["suggested_redline"] = (
                "Each party liability shall not exceed fees paid in the preceding twelve months."
            )
        response = client.patch(f"/api/reports/{rid}/clauses/{cid}", json=payload)
        assert response.status_code == 200
        changed = response.json()["clauses"][2]
        assert changed["redline_status"] == state
        if state == "edited":
            assert changed["suggested_redline"] == payload["suggested_redline"]
        if state == "rejected":
            assert changed["word_diff"] == [
                {"type": "equal", "text": changed["original_text"]}
            ]
    blob = client.get(f"/api/reports/{rid}/export-docx")
    assert blob.status_code == 200 and blob.headers["content-type"].startswith(
        "application/vnd.openxmlformats"
    )
    assert "attachment" in blob.headers["content-disposition"]
    with ZipFile(io.BytesIO(blob.content)) as archive:
        assert b"<w:ins" in archive.read("word/document.xml")
    assert (
        client.patch(
            f"/api/reports/{rid}/clauses/missing", json={"redline_status": "accepted"}
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/reports/{rid}/clauses/{cid}",
            json={"redline_status": "edited", "suggested_redline": " "},
        ).status_code
        == 422
    )
    assert client.get("/api/reports/" + "0" * 32).status_code == 404
    assert client.get("/api/reports/invalid").status_code == 404


def test_semantic_revision_reassessment_and_word_diff(client):
    original = upload(client)
    revised = upload(client, "Sample_MSA.txt")
    response = client.post(
        "/api/revisions/compare",
        data={
            "original_path": original,
            "revised_path": revised,
            "document_type": "MSA",
        },
    )
    assert response.status_code == 200, response.text
    rows = {r["heading"]: r for r in response.json()["comparisons"]}
    assert rows["Limitation of Liability"]["status"] == "Resolved (Compliant)"
    assert rows["Indemnification"]["new_risk_level"] == "Low"
    assert rows["Governing Law"]["status"] == "Resolved (Compliant)"
    assert rows["Termination"]["status"] == "Added"
    assert rows["Fees and Payment"]["status"] == "Resolved (Compliant)"
    assert any(
        t["type"] == "delete" for t in rows["Limitation of Liability"]["word_diff"]
    )
    response = client.post(
        "/api/revisions/compare",
        data={"original_path": revised, "revised_path": original},
    )
    rows = {r["heading"]: r for r in response.json()["comparisons"]}
    assert rows["Termination"]["status"] == "Removed"
    assert rows["Termination"]["word_diff"][0]["type"] == "delete"
    assert rows["Indemnification"]["status"] == "Changed - Residual Risk (High)"


def test_identical_revision_is_no_material_change(client):
    path = upload(client)
    response = client.post(
        "/api/revisions/compare", data={"original_path": path, "revised_path": path}
    )
    assert all(
        r["status"] == "No Material Text Change" for r in response.json()["comparisons"]
    )


def test_settings_diagnostics_and_secret_redaction(client):
    initial = client.get("/api/settings")
    assert initial.status_code == 200 and initial.json()["llm_provider"] == "mock"
    response = client.post(
        "/api/settings",
        json={
            "llm_provider": "openai",
            "llm_model": "test-model",
            "openai_api_key": "a-secret-value",
        },
    )
    assert response.status_code == 200
    assert (
        response.json()["llm_model"] == "test-model"
        and response.json()["api_keys_configured"]["openai"]
    )
    assert (
        "a-secret-value" not in response.text
        and "a-secret-value" not in client.get("/api/settings").text
    )
    assert (
        client.post("/api/settings", json={"llm_provider": "invalid"}).status_code
        == 422
    )
    assert (
        client.post("/api/settings", json={"embedding_provider": "invalid"}).status_code
        == 422
    )
    client.post("/api/settings", json={"llm_provider": "mock"})
    assert client.post("/api/settings/test-llm").json()["result"]["mode"] == "mock"
    assert client.post("/api/settings/test-embeddings").json()["dimensions"] == 384


def test_embedding_settings_update_invalidate_index(client):
    response = client.post(
        "/api/settings",
        json={"embedding_provider": "openai", "embedding_model": "other-embedding"},
    )
    assert response.json()["embedding_model"] == "other-embedding"
    with pytest.raises(RuntimeError, match="mismatch"):
        HybridRetriever(str(main.BASE / "indexes"))
    assert client.post("/api/settings/test-embeddings").status_code == 400
    client.post(
        "/api/settings",
        json={
            "embedding_provider": "local",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        },
    )
    assert client.post("/api/settings/test-embeddings").status_code == 200


def test_invalid_uploads_and_paths(client):
    for endpoint in ("/api/contracts/upload", "/api/playbook/upload"):
        assert (
            client.post(endpoint, files={"file": ("bad.exe", b"bad")}).status_code
            == 400
        )
    assert (
        client.post(
            "/api/review/analyze", data={"path": "/nonexistent.txt"}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/review/analyze",
            data={"path": str(SAMPLES / "Sample_MSA.txt"), "document_type": "unknown"},
        ).status_code
        == 422
    )
    assert (
        client.post("/api/playbook/index", data={"path": "/nonexistent.md"}).status_code
        == 400
    )


def test_readiness_is_deterministic_bounded_and_monotonic():
    covered = [{"status": "Covered"}]
    low = main.score_contract([{"risk_level": "Low"}], covered, [])
    high = main.score_contract([{"risk_level": "High"}], covered, [])
    missing = main.score_contract(
        [{"risk_level": "High"}], [{"status": "Not Covered"}], [{"risk_level": "High"}]
    )
    assert low == (100, "Low")
    assert 0 <= missing[0] < high[0] < low[0] <= 100
    assert high[1] == missing[1] == "High"
    assert main.score_contract([{"risk_level": "Low"}], [], []) == (0, "Medium")


def test_startup_rebuild_preserves_active_rules(client):
    config = main.BASE / "indexes/embedding_config.json"
    metadata = json.loads(config.read_text())
    metadata["model"] = "old-embedding-model"
    config.write_text(json.dumps(metadata))
    chunks = main.BASE / "indexes/chunks.json"
    active_rules = json.loads(chunks.read_text())
    active_rules[0]["source"] = "custom-company-policy.md"
    chunks.write_text(json.dumps(active_rules))
    assert not client.get("/api/playbook/index-status").json()["indexed"]
    main.ensure_default_playbook_indexed()
    assert client.get("/api/playbook/index-status").json()["indexed"]
    assert (
        client.get("/api/playbook/rules").json()["rules"][0]["source"]
        == "custom-company-policy.md"
    )
