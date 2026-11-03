import os
import json
import uuid
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from server import app
from scripts.record_baseline_conversations import TEST_SCENARIOS

client = TestClient(app)

def run_enhanced_evaluation():
    results = []
    print(f"Starting Enhanced Engine Evaluation for {len(TEST_SCENARIOS)} scenarios...\n")

    for idx, sc in enumerate(TEST_SCENARIOS, 1):
        chat_id = f"enhanced_test_{idx:02d}_{uuid.uuid4().hex[:6]}"
        print(f"[{idx}/{len(TEST_SCENARIOS)}] Evaluating {sc['id']}: {sc['title']}")
        
        scenario_record = {
            "scenario_id": sc["id"],
            "category": sc["category"],
            "title": sc["title"],
            "expected_behavior": sc["expected_behavior"],
            "turns_recorded": []
        }

        for turn_idx, query in enumerate(sc["turns"], 1):
            req_body = {
                "chat_id": chat_id,
                "query": query,
                "user_profile": {
                    "employment": "Salaried",
                    "cibil_score": 750,
                    "income": None,
                    "requested_amount": None,
                    "category": None,
                    "sector": None
                }
            }

            res = client.post("/api/chat", json=req_body)
            if res.status_code == 200:
                data = res.json()
                candidate_names = [
                    f"{c.get('metadata', {}).get('institution')} - {c.get('metadata', {}).get('scheme_name')}"
                    for c in data.get("candidates", [])
                ]
                
                scenario_record["turns_recorded"].append({
                    "turn_index": turn_idx,
                    "user_query": query,
                    "detected_intent": data.get("intent"),
                    "response_type": data.get("response_type"),
                    "candidates_count": len(data.get("candidates", [])),
                    "candidates_summary": candidate_names,
                    "has_clarification": bool(data.get("clarification")),
                    "clarification_summary": {
                        "category": data.get("clarification", {}).get("category") if data.get("clarification") else None,
                        "questions_count": len(data.get("clarification", {}).get("next_questions", [])) if data.get("clarification") else 0,
                        "missing_fields": data.get("clarification", {}).get("blocking_missing_fields", []) if data.get("clarification") else []
                    } if data.get("clarification") else None,
                    "discovery_profile": data.get("discovery_profile"),
                    "has_decision_trace": bool(data.get("decision_trace")),
                    "response_text": data.get("final_response")
                })
            else:
                scenario_record["turns_recorded"].append({
                    "turn_index": turn_idx,
                    "user_query": query,
                    "error": f"HTTP {res.status_code}: {res.text}"
                })

        results.append(scenario_record)

    out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "enhanced_evaluation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Enhanced evaluation complete! Saved to {out_path}")
    return results

def generate_comparison_report(baseline_path: str, enhanced_path: str):
    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)
    with open(enhanced_path, "r", encoding="utf-8") as f:
        enhanced_data = json.load(f)

    comparison = []

    for b_sc, e_sc in zip(baseline_data, enhanced_data):
        sc_id = b_sc["scenario_id"]
        title = b_sc["title"]
        category = b_sc["category"]
        expected = b_sc["expected_behavior"]

        turns_comparison = []
        for b_turn, e_turn in zip(b_sc["turns_recorded"], e_sc["turns_recorded"]):
            t_idx = b_turn["turn_index"]
            q = b_turn["user_query"]

            b_intent = b_turn.get("detected_intent")
            b_cand_count = b_turn.get("candidates_count", 0)
            b_cands = b_turn.get("candidates_summary", [])
            b_text = b_turn.get("response_text", "")

            e_intent = e_turn.get("detected_intent")
            e_res_type = e_turn.get("response_type")
            e_cand_count = e_turn.get("candidates_count", 0)
            e_cands = e_turn.get("candidates_summary", [])
            e_clar = e_turn.get("clarification_summary")
            e_prof = e_turn.get("discovery_profile")
            e_text = e_turn.get("response_text", "")

            # Analyze key behavioral shift
            insights = []
            if b_cand_count > 0 and e_cand_count == 0 and e_res_type == "CLARIFICATION":
                insights.append("Eliminated premature candidate dump on incomplete criteria; engaged consultative clarification.")
            elif b_intent == "EMI_CALCULATOR" and "tenure" not in q.lower() and "5 years" in b_text.lower():
                if "15 Years" in e_text and "20 Years" in e_text:
                    insights.append("Eliminated silent 5-year tenure assumption; replaced with multi-tenure scenario matrix.")
            elif b_intent == "EMI_CALCULATOR" and ("existing" in q.lower() or "salary" in q.lower()):
                if e_intent != "EMI_CALCULATOR":
                    insights.append("Fixed routing false positive where stating income/existing EMIs was misclassified as EMI calculator.")

            # Duplicate lender check
            b_institutions = [c.split(" - ")[0] for c in b_cands if " - " in c]
            e_institutions = [c.split(" - ")[0] for c in e_cands if " - " in c]
            if len(b_institutions) > 1 and len(set(b_institutions)) < len(b_institutions):
                if len(e_institutions) > 1 and len(set(e_institutions)) == len(e_institutions):
                    insights.append("Eliminated duplicate lender candidates; ensured diverse institutional coverage.")

            turns_comparison.append({
                "turn": t_idx,
                "query": q,
                "baseline": {
                    "intent": b_intent,
                    "candidates_count": b_cand_count,
                    "candidates": b_cands,
                    "sample_snippet": b_text[:140] + "..." if len(b_text) > 140 else b_text
                },
                "enhanced": {
                    "intent": e_intent,
                    "response_type": e_res_type,
                    "candidates_count": e_cand_count,
                    "candidates": e_cands,
                    "clarification": e_clar,
                    "profile_state": e_prof,
                    "sample_snippet": e_text[:140] + "..." if len(e_text) > 140 else e_text
                },
                "key_improvements": insights
            })

        comparison.append({
            "scenario_id": sc_id,
            "title": title,
            "category": category,
            "expected_behavior": expected,
            "turns": turns_comparison
        })

    comp_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "comparison_evaluation_summary.json")
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    print(f"✓ Comparison summary report saved to {comp_path}")
    return comparison

if __name__ == "__main__":
    run_enhanced_evaluation()
    base_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "baseline_evaluation_report.json")
    enh_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "enhanced_evaluation_report.json")
    generate_comparison_report(base_file, enh_file)

