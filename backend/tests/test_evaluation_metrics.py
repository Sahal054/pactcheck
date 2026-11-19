"""A transparent fixture benchmark, not a claim of general or live-LLM legal accuracy."""

import asyncio
import json
from datetime import datetime, timezone
from app.services.documents.parser import extract_clauses
from app.services.analysis.intelligence import cross_clause_findings
from conftest import ROOT, SAMPLES


def test_ground_truth_benchmark(reviewer):
    truth = json.loads((SAMPLES / "ground_truth.json").read_text())
    tp = tn = fp = fn = hits = queries = cross_fp = 0
    details = []
    for filename, expected in truth["contracts"].items():
        clauses = extract_clauses(str(SAMPLES / filename))
        assert len(clauses) == len(expected["clauses"])
        assessments = asyncio.run(
            reviewer.assess_many_async(clauses, expected["document_type"])
        )
        for c, a, label in zip(clauses, assessments, expected["clauses"]):
            assert (c["clause_number"], c["heading"]) == (
                label["number"],
                label["heading"],
            )
            actual = a["risk_level"] in {"High", "Medium"}
            # Unclear responses never get counted as successful negative predictions.
            assert a["risk_level"] != "Unclear", (
                filename,
                c["heading"],
                a["explanation"],
            )
            tp += int(label["positive"] and actual)
            tn += int(not label["positive"] and not actual)
            fp += int(not label["positive"] and actual)
            fn += int(label["positive"] and not actual)
            if label["rule"]:
                queries += 1
                hits += int(
                    label["rule"]
                    in {
                        e["rule_id"]
                        for e in reviewer._retrieve(c, expected["document_type"])
                    }
                )
            details.append(
                {
                    "contract": filename,
                    "clause_number": c["clause_number"],
                    "heading": c["heading"],
                    "expected_positive": label["positive"],
                    "actual_risk": a["risk_level"],
                    "rule_ids": a["applicable_rule_ids"],
                }
            )
        cross = cross_clause_findings(
            clauses, assessments, document_type=expected["document_type"]
        )
        relationships = {f["relationship"] for f in cross}
        cross_fp += len(
            relationships - set(expected["expected_cross_clause_relationships"])
        )
        assert relationships == set(expected["expected_cross_clause_relationships"])
        if filename == "Sample_High_Risk_MSA.txt":
            assert "Liability clause without indemnification" not in relationships
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    metrics = {
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": 2 * precision * recall / (precision + recall),
        "Specificity": tn / (tn + fp),
        "FPR": fp / (fp + tn),
        "FNR": fn / (fn + tp),
        "Hit@K": hits / queries,
    }
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "mock deterministic offline feature hashing",
        "scope": "All 20 supplied numbered clauses (7 high-risk MSA + 8 MSA + 5 NDA); fixture accuracy only.",
        "confusion_matrix": {"TP": tp, "TN": tn, "FP": fp, "FN": fn},
        "total_clauses": len(details),
        "metrics": metrics,
        "rag_k": 3,
        "rag_hits": hits,
        "rag_queries": queries,
        "cross_clause_false_positives": cross_fp,
        "clause_results": details,
    }
    destination = ROOT / "backend/data/evaluation_metrics.json"
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print("\nConfusion matrix (positive = clause policy deviation)")
    print("                  Predicted +  Predicted -")
    print(f"Actual positive   TP = {tp:<7} FN = {fn}")
    print(f"Actual negative   FP = {fp:<7} TN = {tn}")
    print("\nMetric                 Value")
    print("----------------------------")
    for name, value in metrics.items():
        print(f"{name:<22} {value:.4f}")
    print(f"Cross-clause FP         {cross_fp}")
    print(f"RAG hits @ K=3          {hits}/{queries}")
    print(f"Total clauses          {len(details)}")
    assert (tp, tn, fp, fn) == (5, 15, 0, 0)
    assert (
        metrics["Precision"]
        == metrics["Recall"]
        == metrics["Accuracy"]
        == metrics["F1"]
        == 1.0
    )
    assert metrics["FPR"] == metrics["FNR"] == 0.0
    assert metrics["Hit@K"] == 1.0 and cross_fp == 0
