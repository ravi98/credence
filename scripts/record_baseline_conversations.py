import os
import json
import uuid
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

# 18 Representative Test Scenarios derived directly from the design document
TEST_SCENARIOS = [
    {
        "id": "SCENARIO_01_SILENT_TENURE_ASSUMPTION",
        "category": "Financial Assumption",
        "title": "Query with loan quantum but unstated tenure and income",
        "turns": [
            "I need a ₹1 crore home loan."
        ],
        "expected_behavior": "Should recognize Home Loan and amount (1 Cr). Should NOT assume tenure or interest rate. Should NOT present premature personalized EMI. Should ask clarifying questions."
    },
    {
        "id": "SCENARIO_02_EMI_WITHOUT_TENURE_OR_RATE",
        "category": "Financial Assumption",
        "title": "EMI calculation query missing tenure and rate",
        "turns": [
            "Calculate EMI for ₹50 lakh."
        ],
        "expected_behavior": "Should ask for tenure and interest rate, or present a clearly labeled illustrative scenario table across multiple tenures. Should never silently assume 5 years or 8.75%."
    },
    {
        "id": "SCENARIO_03_EXISTING_OBLIGATIONS_HANDLING",
        "category": "Financial Assumption",
        "title": "Declared income with substantial existing EMIs",
        "turns": [
            "I earn ₹1.5 lakh monthly and have ₹20,000 in existing EMIs. Can I get a home loan?"
        ],
        "expected_behavior": "Must capture existing EMI obligations (₹20k) and net income (₹1.5L). Must calculate available FOIR headroom (max 50-60% minus 20k) rather than assuming zero debt."
    },
    {
        "id": "SCENARIO_04_MULTI_TURN_REQUIREMENT_PERSISTENCE",
        "category": "Conversation State",
        "title": "Progressive multi-turn requirement discovery",
        "turns": [
            "I need a ₹50 lakh home loan.",
            "I'm salaried, earning ₹1.2 lakh monthly.",
            "I have existing EMIs of ₹15,000."
        ],
        "expected_behavior": "All 3 details (amount=50L, employment=Salaried, income=1.2L, existing_emi=15k) must persist across turns without resetting or forgetting prior turns."
    },
    {
        "id": "SCENARIO_05_EXPLICIT_CORRECTION_HANDLING",
        "category": "Conversation State",
        "title": "Customer corrects previously stated financial figure",
        "turns": [
            "My monthly income is ₹1.2 lakh, looking for 40 lakh loan.",
            "Actually, my income is ₹1.5 lakh, not ₹1.2 lakh."
        ],
        "expected_behavior": "Should gracefully acknowledge the correction, update income to ₹1.5 lakh, and not retain the old ₹1.2 lakh figure in subsequent calculations."
    },
    {
        "id": "SCENARIO_06_UNKNOWN_CIBIL_TOLERANCE",
        "category": "Conversation State",
        "title": "Customer does not know their credit score",
        "turns": [
            "I want to explore home loans around 45 lakhs, salary 90k, but I don't know my CIBIL score."
        ],
        "expected_behavior": "Should continue discovery with an appropriate limitation note. Should never block the user or invent a random score (e.g. 750)."
    },
    {
        "id": "SCENARIO_07_LENDER_DIVERSITY_COVERAGE",
        "category": "Candidate Retrieval",
        "title": "Broad recommendation seeking public and private lenders",
        "turns": [
            "Find suitable home loans from public and private banks for 60 lakh loan."
        ],
        "expected_behavior": "Should explore the broader 163-scheme catalog and present diverse public/private options rather than repeatedly returning the same top 2 Chroma chunks."
    },
    {
        "id": "SCENARIO_08_CHALLENGING_A_RECOMMENDATION",
        "category": "Decision Trace",
        "title": "Customer questions why a specific bank was omitted",
        "turns": [
            "Recommend top home loan options for ₹75 lakh.",
            "Why wasn't Indian Bank recommended?"
        ],
        "expected_behavior": "Must not invent retrospective excuses (like 'I prefer private banks'). Must refer to actual retrieval boundary or criteria trace."
    },
    {
        "id": "SCENARIO_09_PREFERENCE_TOTAL_INTEREST_VS_EMI",
        "category": "Ranking Engine",
        "title": "Customer explicitly prioritizes lowest total interest cost",
        "turns": [
            "I earn 1.5L and want a 50L home loan. I want the lowest total interest, not the lowest EMI."
        ],
        "expected_behavior": "Should rank options prioritizing lowest interest rate and shorter tenure over maximum tenure options with lower monthly EMIs."
    },
    {
        "id": "SCENARIO_10_MAX_COMFORTABLE_EMI_CONSTRAINT",
        "category": "Ranking Engine",
        "title": "Customer sets an absolute ceiling on monthly EMI",
        "turns": [
            "I can pay a maximum EMI of ₹35,000 for a ₹50 lakh home loan. What can I get?"
        ],
        "expected_behavior": "Should calculate that a ₹50L loan at 8.5% over 20 years requires ~₹43,391 EMI, which exceeds ₹35k. Should guide user to increase tenure to 25-30 years or adjust loan quantum to ~₹40L."
    },
    {
        "id": "SCENARIO_11_GENERAL_EDUCATION_INTENT",
        "category": "Intent Routing",
        "title": "General financial/regulatory concept inquiry",
        "turns": [
            "What is FOIR and how do banks calculate it?"
        ],
        "expected_behavior": "Should answer directly with educational facts (Fixed Obligation to Income Ratio, 50% cap). Should NOT launch the full loan discovery questionnaire."
    },
    {
        "id": "SCENARIO_12_SPECIFIC_PRODUCT_QUERY_INTENT",
        "category": "Intent Routing",
        "title": "Inquiry about a specific banking product feature",
        "turns": [
            "Explain SBI MaxGain home loan and how the overdraft facility works."
        ],
        "expected_behavior": "Should retrieve and explain the specific SBI MaxGain scheme and its savings account interest offset. Should NOT launch a borrower questionnaire."
    },
    {
        "id": "SCENARIO_13_LOAN_COMPARISON_INTENT",
        "category": "Intent Routing",
        "title": "Side-by-side comparison between two named banks",
        "turns": [
            "Compare SBI Regular Home Loan vs HDFC Standard Home Loan."
        ],
        "expected_behavior": "Should produce a clean, structured comparison table (interest rates, benchmarks, processing fees, tenure) for both institutions."
    },
    {
        "id": "SCENARIO_14_DOCUMENTATION_ELIGIBILITY_QUERY",
        "category": "Eligibility & Policy",
        "title": "Documentation query for salaried home loan",
        "turns": [
            "What documents are required for a salaried home loan application?"
        ],
        "expected_behavior": "Should list mandatory KYC, income proofs (3 months payslips, 6 months bank statement, Form 16), and property documents factually."
    },
    {
        "id": "SCENARIO_15_GENERIC_INCOME_NORMS",
        "category": "Eligibility & Policy",
        "title": "Query regarding minimum salary benchmarks",
        "turns": [
            "What is the generic minimum salary required for home loans across banks?"
        ],
        "expected_behavior": "Should explain public bank norms (₹15k-₹20k), private bank norms (₹25k-₹30k), and affordable housing entry thresholds (₹10k-₹12k)."
    },
    {
        "id": "SCENARIO_16_EDUCATION_LOAN_DISCOVERY",
        "category": "Category Specific",
        "title": "Education loan inquiry for overseas studies",
        "turns": [
            "I need an education loan for MS in the US."
        ],
        "expected_behavior": "Should ask education-specific questions: university/course ranking, estimated total cost, co-borrower/parent income, and collateral availability."
    },
    {
        "id": "SCENARIO_17_PERSONAL_LOAN_DISCOVERY",
        "category": "Category Specific",
        "title": "Urgent personal loan inquiry",
        "turns": [
            "I need an urgent personal loan of ₹5 lakhs."
        ],
        "expected_behavior": "Should ask personal loan-specific questions: salaried vs self-employed, employer name, net monthly income, and required repayment horizon."
    },
    {
        "id": "SCENARIO_18_CAR_LOAN_DISCOVERY",
        "category": "Category Specific",
        "title": "Vehicle loan inquiry for a specific car",
        "turns": [
            "I want a car loan for a new Hyundai Creta."
        ],
        "expected_behavior": "Should ask car loan-specific questions: on-road price, down payment margin, new vs used, and preferred tenure (up to 7 years)."
    }
]

def run_baseline_suite():
    results = []
    print(f"Starting baseline recording for {len(TEST_SCENARIOS)} scenarios on CURRENT engine...\n")

    for idx, sc in enumerate(TEST_SCENARIOS, 1):
        chat_id = f"baseline_test_{idx:02d}_{uuid.uuid4().hex[:6]}"
        print(f"[{idx}/{len(TEST_SCENARIOS)}] Running {sc['id']}: {sc['title']}")
        
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
                candidate_names = [f"{c.get('metadata', {}).get('institution')} - {c.get('metadata', {}).get('scheme_name')}" for c in data.get("candidates", [])]
                
                scenario_record["turns_recorded"].append({
                    "turn_index": turn_idx,
                    "user_query": query,
                    "detected_intent": data.get("intent"),
                    "candidates_count": len(data.get("candidates", [])),
                    "candidates_summary": candidate_names,
                    "response_text": data.get("final_response")
                })
            else:
                scenario_record["turns_recorded"].append({
                    "turn_index": turn_idx,
                    "user_query": query,
                    "error": f"HTTP {res.status_code}: {res.text}"
                })

        results.append(scenario_record)

    out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "baseline_evaluation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Baseline recording complete! Saved to {out_path}")
    return results

if __name__ == "__main__":
    run_baseline_suite()

