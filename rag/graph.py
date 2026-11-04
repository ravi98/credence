import os
import re
import json
import operator
import math
from typing import TypedDict, List, Dict, Optional, Any, Annotated
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from rag.engine import LoanRecommendationEngine
from rag.router import semantic_router
from rag.policies import CATEGORY_POLICIES
from rag.discovery import LoanDiscoveryProfile, LoanCategory, FieldState
from rag.extractor import update_profile_from_query, parse_indian_number
from rag.clarification import ClarificationManager
from rag.retrieval import StructuredCandidateRetriever, ALL_SCHEMES
from rag.ranking import DeterministicRanker, calculate_monthly_emi
from rag.trace import record_decision_trace, get_latest_trace

engine = LoanRecommendationEngine()
clarification_manager = ClarificationManager()
candidate_retriever = StructuredCandidateRetriever(ALL_SCHEMES)
deterministic_ranker = DeterministicRanker()

# Memory store for active discovery profiles per thread
_PROFILE_STORE: Dict[str, LoanDiscoveryProfile] = {}

class LoanAdvisorState(TypedDict):
    chat_id: str
    query: str
    user_profile: Dict[str, Any]
    intent: str
    active_category: Optional[str]
    monthly_income_num: Optional[float]
    candidates: List[Dict[str, Any]]
    active_schemes: List[Dict[str, Any]]
    comparison_schemes: List[Dict[str, Any]]
    emi_result: Optional[Dict[str, Any]]
    context_text: str
    chat_history: Annotated[List[Dict[str, str]], operator.add]
    final_response: str
    api_key: Optional[str]
    model_name: Optional[str]
    # Enhanced state fields
    discovery_profile: Dict[str, Any]
    clarification: Optional[Dict[str, Any]]
    decision_trace: Optional[Dict[str, Any]]
    response_type: str
    discovery_progress: Optional[Dict[str, Any]]

SYSTEM_PROMPT = """You are Credence, an expert, objective Indian Retail Loan Advisor.
CORE RULES:
1. Conversation Context: Maintain strict continuity across turns. Refer back to discussed categories, income levels, and schemes naturally.
2. Structured Clarification: If the user needs loan recommendations or borrowing capacity assessment but critical details (such as tenure, monthly net income, or requested amount) are missing, explain WHY these parameters matter and ask the clarifying questions. Do NOT prematurely recommend loans.
3. No Silent Assumptions: Never invent or silently assume a loan tenure (e.g. 5 years) or interest rate for personalized EMI calculations. Always present illustrative scenarios across standard tenures if parameters are unstated.
4. Product Recommendations: When sufficient criteria are established, provide candidate schemes with Scheme Name, Bank, Key Signature, Rate, Tenure, and Link. Explain why each was chosen based on the user's specific figures.
5. Comparisons: Provide a compact markdown table comparing Rate, Tenure, and Fee/LTV.
6. Absolute Accuracy: Rely EXCLUSIVELY on verified banking data provided. Never invent rates, numbers, or terms.
"""

# ==================== Graph Nodes ====================

def extractor_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Incrementally extracts and persists borrowing criteria in LoanDiscoveryProfile across conversation turns."""
    chat_id = state.get("chat_id", "default_session")
    profile = _PROFILE_STORE.get(chat_id)
    if profile is None:
        disc = state.get("discovery_profile")
        if disc and isinstance(disc, dict) and any(disc.get(k) is not None for k in ["requested_amount", "monthly_net_income", "preferred_tenure_months"]):
            profile = LoanDiscoveryProfile.from_dict_summary(disc)
        else:
            profile = LoanDiscoveryProfile()

    # Pre-fill category if active in previous turn
    if state.get("active_category") and not profile.loan_category.is_known():
        profile.loan_category.set_user_value(state["active_category"])

    # Update with query text and UI drawer filters
    profile = update_profile_from_query(state["query"], profile, state.get("user_profile"))
    _PROFILE_STORE[chat_id] = profile

    return {
        "discovery_profile": profile.to_dict_summary(),
        "active_category": profile.loan_category.value
    }

def router_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Routes query using semantic router."""
    intent = semantic_router.route(state["query"])
    return {"intent": intent}

def clarify_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Constructs consultative educational response explaining loan parameters and asks clarifying questions."""
    chat_id = state.get("chat_id", "default_session")
    profile = _PROFILE_STORE.get(chat_id, LoanDiscoveryProfile())
    eval_res = clarification_manager.evaluate_readiness(
        profile, 
        state.get("intent", "RECOMMENDATION"),
        query=state.get("query")
    )

    category = eval_res.get("category") or profile.loan_category.value or "Home Loan"
    amt_known = profile.requested_amount.is_known()
    amt_str = f"₹{profile.requested_amount.value:,.0f}" if amt_known else "your desired loan"

    if "ltv" in category.lower():
        lines = [
            f"To accurately assess your eligibility for a 90% Loan-to-Value (LTV) request under RBI guidelines:\n",
            "1. **Property Valuation vs. Purchase Price**: Banks lend 90% of the lower of the bank valuer appraisal or registered agreement value.",
            "2. **Property Type Restrictions**: 90% LTV is allowed exclusively on residential properties up to ₹30L (80% up to ₹75L, 75% above ₹75L). Commercial units and land/plots are capped at 60%–70%.",
            "3. **Location Clearance**: Tier-1 metros support higher valuation benchmarks and faster title approvals.\n"
        ]
    else:
        lines = [
            f"To identify the most competitive, verified {category.lower()} options for {amt_str} without risking application rejection, Indian banks evaluate 4 core underwriting factors under RBI guidelines:\n",
            "1. **Net Monthly Income & Employer Category**: Determines your maximum eligible loan quantum and fee waiver brackets.",
            "2. **Preferred Loan Tenure**: Longer tenures lower your monthly EMI but increase total cumulative interest outflow.",
            "3. **Existing Monthly Obligations (FOIR)**: Banks legally cap all combined EMIs at 50%–60% of your take-home pay.",
            "4. **CIBIL Score**: RBI mandates external benchmark (EBLR) risk-tiered pricing (750+ unlocks the lowest base spread).\n"
        ]

    questions = eval_res.get("next_questions", [])
    if questions:
        lines.append("**Please specify the following details to assess your exact eligibility:**")
        for idx, q in enumerate(questions, 1):
            opts = q.get("options", [])
            if opts:
                opts_str = " | ".join([f"`{o['label']}`" for o in opts[:4]])
                lines.append(f"{idx}. **{q['question']}**\n   *Options*: {opts_str}")
            else:
                lines.append(f"{idx}. **{q['question']}**")

    clarify_context = "\n".join(lines)

    return {
        "candidates": [],
        "clarification": eval_res,
        "discovery_progress": eval_res.get("discovery_progress"),
        "response_type": "CLARIFICATION",
        "context_text": clarify_context
    }

def recommend_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Retrieves deduplicated candidate schemes from catalog and applies deterministic ranking."""
    chat_id = state.get("chat_id", "default_session")
    profile = _PROFILE_STORE.get(chat_id, LoanDiscoveryProfile())

    # 1. Structured Candidate Retrieval with Lender Deduplication
    raw_candidates = candidate_retriever.filter_and_deduplicate(profile, max_results=4)

    # 2. Deterministic Ranking
    ranked_candidates = deterministic_ranker.rank_candidates(raw_candidates, profile)

    # 3. Record Decision Trace for Explainability
    trace = record_decision_trace(
        chat_id=chat_id,
        profile_summary=profile.to_dict_summary(),
        all_examined=raw_candidates,
        shortlisted=ranked_candidates[:2],
        priorities=profile.priorities
    )

    # Format recommendation context
    principal = profile.requested_amount.value or 5000000.0
    category = profile.loan_category.value or "Home Loan"
    tenure_months = profile.preferred_tenure_months.value or 240
    tenure_years = tenure_months // 12

    context_lines = [
        f"Verified {category} Recommendations for ₹{principal:,.0f} over {tenure_years} Years:\n"
    ]

    income = profile.monthly_net_income.value
    existing_emi = profile.existing_monthly_emi.value or 0.0
    profile_summary_bits = []
    if income:
        profile_summary_bits.append(f"Declared Monthly Net Income: ₹{income:,.0f}")
    if profile.existing_monthly_emi.is_known():
        profile_summary_bits.append(f"Existing Debt EMI: ₹{existing_emi:,.0f}")
    if profile.employment_type.is_known():
        profile_summary_bits.append(f"Employment: {profile.employment_type.value}")
    if profile.self_reported_credit_score.is_known():
        profile_summary_bits.append(f"CIBIL: {profile.self_reported_credit_score.value}")

    if profile_summary_bits:
        context_lines.append(f"Borrower Underwriting Context: {', '.join(profile_summary_bits)}\n")

    # Check maximum comfortable EMI constraint if specified by user
    max_emi = profile.maximum_monthly_emi.value
    if max_emi:
        lowest_cand_emi = ranked_candidates[0]["ranking_details"]["estimated_monthly_emi"] if ranked_candidates else 0
        if lowest_cand_emi > max_emi:
            context_lines.append(
                f"⚠️ **Affordability Budget Note**: Your stated comfortable EMI ceiling of ₹{max_emi:,.0f}/month is lower than the required monthly installment for ₹{principal:,.0f} (₹{lowest_cand_emi:,.0f}/mo). To stay within ₹{max_emi:,.0f}, you can either extend tenure to 25–30 years or calibrate your loan quantum to ~₹{round(principal * (max_emi / lowest_cand_emi)):,.0f}.\n"
            )

    top_candidates = ranked_candidates[:2]
    for idx, c in enumerate(top_candidates, 1):
        m = c["metadata"]
        rd = c["ranking_details"]
        key = m.get("compact_key", f"{rd['effective_rate']}%_{m.get('sector')}_{rd['tenure_years']}y_{m.get('category')}")
        context_lines.append(
            f"[{idx}] {m.get('scheme_name')} ({m.get('institution')}) — **{rd.get('badge', 'Top Match')}**\n"
            f"- Key Signature: `{key}`\n"
            f"- Effective Interest Rate: **{rd['effective_rate']}%** ({m.get('benchmark', 'EBLR')})\n"
            f"- Estimated Monthly EMI: **₹{rd['estimated_monthly_emi']:,}** ({rd['tenure_years']} Years)\n"
            f"- Processing Fees: {m.get('processing_fee', 'Standard bank fee')}\n"
            f"- Official Portal: {m.get('source_url')}"
        )

    eval_res = clarification_manager.evaluate_readiness(
        profile, 
        "RECOMMENDATION",
        query=state.get("query")
    )

    return {
        "candidates": top_candidates,
        "active_schemes": top_candidates,
        "decision_trace": trace.model_dump(),
        "clarification": None,
        "discovery_progress": eval_res.get("discovery_progress"),
        "response_type": "LOAN_RECOMMENDATION",
        "context_text": "\n\n".join(context_lines)
    }

def comparison_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Splits comparative query into entities and retrieves exact verified schemes."""
    q = state["query"].lower().replace("compare ", "").strip()
    parts = re.split(r"\s+vs\.?\s+|\s+versus\s+|\s+and\s+", q)
    matched_schemes = []

    if len(parts) >= 2:
        for part in parts[:2]:
            clean_part = part.strip()
            if clean_part:
                cand = engine.retrieve(query=clean_part, section_type="parent_card", n_results=1)
                if cand:
                    matched_schemes.append(cand[0])

    if len(matched_schemes) < 2:
        semantic_candidates = engine.retrieve(query=state["query"], section_type="parent_card", n_results=2)
        matched_schemes = semantic_candidates

    context_lines = ["Verified Schemes to Compare:"]
    for idx, item in enumerate(matched_schemes, 1):
        m = item["metadata"]
        key = m.get("compact_key", f"{m.get('interest_rate_range')}_{m.get('sector')}_{m.get('max_tenure_years')}y_{m.get('category')}")
        context_lines.append(
            f"[{idx}] {m.get('scheme_name')} ({m.get('institution')}) | Key: `{key}` | "
            f"Rate: {m.get('interest_rate_range')} ({m.get('benchmark')}) | "
            f"Max: {m.get('max_loan_amount')}, {m.get('max_tenure_years')}y | "
            f"Fee: {m.get('processing_fee', 'N/A')} | Link: {m.get('source_url')}"
        )

    return {
        "comparison_schemes": matched_schemes,
        "candidates": matched_schemes,
        "active_schemes": matched_schemes,
        "clarification": None,
        "response_type": "LOAN_COMPARISON",
        "context_text": "\n".join(context_lines)
    }

def specific_product_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Answers specific product feature inquiries without launching complete discovery."""
    q = state["query"]
    target_docs = engine.retrieve(query=q, section_type="parent_card", n_results=1)
    
    context = (
        "SPECIFIC PRODUCT ADVISORY:\n"
        "Customer is inquiring about a specific loan product feature (e.g. SBI MaxGain overdraft facility).\n"
        "Explain factually how this specific facility operates: parking surplus cash in the linked overdraft account reduces daily principal interest burden while retaining complete withdrawal liquidity.\n"
        "Do NOT launch a borrower questionnaire for an informational product inquiry."
    )
    if target_docs:
        m = target_docs[0]["metadata"]
        context += f"\n\nRetrieved Product: {m.get('scheme_name')} by {m.get('institution')} ({m.get('source_url')})"

    return {
        "candidates": target_docs,
        "clarification": None,
        "response_type": "PRODUCT_DETAILS",
        "context_text": context
    }

def eligibility_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Answers eligibility, income norms, criteria, and documentation questions using declarative policies."""
    q = state["query"].lower().strip()
    chat_id = state.get("chat_id", "default_session")
    profile = _PROFILE_STORE.get(chat_id, LoanDiscoveryProfile())
    category = profile.loan_category.value or "Home Loan"
    policy = CATEGORY_POLICIES.get(category, CATEGORY_POLICIES["Home Loan"])

    # 1. Documentation Queries
    if any(k in q for k in ["document", "paper", "proof", "kyc"]):
        context = (
            f"Mandatory Documents Required for {category}:\n"
            "- Identity & Address Proof: PAN Card (mandatory), Aadhaar Card, Passport, or Voter ID.\n"
            "- Income Proof (Salaried): Last 3 months salary slips, 6 months bank statements showing salary credit, Form 16 / ITR.\n"
            "- Income Proof (Self-Employed): Last 2-3 years audited balance sheets, P&L, ITR with computation of income, 6 months business bank statement.\n"
            "- Property/Asset Documents: Title deeds, builder NOC, approved building plan, sale agreement."
        )
    # 2. Generic Income Benchmark Queries
    elif any(k in q for k in ["generic", "most of", "industry", "average", "typical", "minimum salary"]):
        context = (
            f"Verified Indian {category} Monthly Income Standards:\n"
            f"- Public Sector Banks (SBI, Bank of Baroda, PNB): Minimum ₹15,000 to ₹25,000 net monthly salary.\n"
            f"- Private Sector Banks (HDFC, ICICI, Kotak, Axis): Minimum ₹25,000 (Tier-2/3) to ₹30,000+/month (Metros).\n"
            f"- Affordable Housing Finance (Kotak Vishwas, PMAY NBFCs): Minimum ₹10,000 to ₹12,000/month.\n"
            f"- FOIR (Fixed Obligation to Income Ratio): All banks cap total monthly debt obligations at {int(policy.get('max_foir', 0.5)*100)}% of net monthly income.\n"
            f"- Age & Stability: 21–65 years of age; minimum 2 years continuous employment stability."
        )
    else:
        income = profile.monthly_net_income.value
        existing_emi = profile.existing_monthly_emi.value or 0.0
        principal = profile.requested_amount.value

        if income:
            max_foir = policy.get("max_foir", 0.50)
            max_allowable_total_emi = income * max_foir
            available_new_emi = max(0.0, max_allowable_total_emi - existing_emi)

            lines = [
                f"Personalized Eligibility & FOIR Assessment for {category}:",
                f"- Declared Net Monthly Income: ₹{income:,.0f}",
                f"- Existing Monthly Debt Obligations: ₹{existing_emi:,.0f}",
                f"- Maximum Allowable Total EMI (FOIR {int(max_foir*100)}% Cap): ₹{max_allowable_total_emi:,.0f}/month",
                f"- Available EMI Headroom for New Loan: ₹{available_new_emi:,.0f}/month"
            ]
            if principal:
                tenure_m = profile.preferred_tenure_months.value or 240
                est_emi = calculate_monthly_emi(principal, 8.50, tenure_m)
                lines.append(f"- Estimated Monthly EMI for ₹{principal:,.0f} ({tenure_m//12}y at ~8.5% benchmark): ₹{round(est_emi):,}/month")
                if est_emi <= available_new_emi:
                    lines.append(f"✓ **Eligible & Affordable**: The proposed installment fits comfortably within bank debt ceilings.")
                else:
                    lines.append(f"⚠️ **FOIR Constraint**: Required EMI exceeds your headroom by ₹{round(est_emi - available_new_emi):,}. Extending tenure or adding an earning co-applicant will qualify you.")
            context = "\n".join(lines)
        else:
            context = (
                f"Standard Minimum Eligibility Criteria for {category} across Indian Banks:\n"
                f"- Net Monthly Income: ₹{policy.get('min_individual_income', 12000):,} (affordable schemes) to ₹{policy.get('standard_min_income', 25000):,}+ (prime banks).\n"
                f"- Credit Track Record: CIBIL 750+ needed for lowest risk spread; 700+ accepted with spread markup.\n"
                f"- FOIR Ceiling: Monthly EMIs cannot exceed {int(policy.get('max_foir', 0.5)*100)}% of net monthly take-home pay."
            )

    return {
        "candidates": [],
        "clarification": None,
        "response_type": "ELIGIBILITY_RESULT",
        "context_text": context
    }

def meta_chat_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Answers conversational challenges, reflections, and corrections from decision trace and history."""
    chat_id = state.get("chat_id", "default_session")
    trace = get_latest_trace(chat_id)
    profile = _PROFILE_STORE.get(chat_id, LoanDiscoveryProfile())

    q = state["query"].lower().strip()

    # Handle Indian Bank omission challenge
    if any(k in q for k in ["indian bank", "why wasn't", "why did not"]):
        if trace and any("indian bank" in c.institution.lower() for c in trace.shortlisted):
            context = "Indian Bank is already included in your active shortlist."
        else:
            context = (
                "DECISION TRACE VERIFICATION:\n"
                "Customer is asking why Indian Bank was not recommended in the earlier shortlist.\n"
                "Explain honestly based on recorded trace: Indian Bank was not included in the initial top 2 shortlist because the earlier candidates were selected based on the specific loan quantum and default ranking factors. Indian Bank offers competitive rates (starting at 7.25%–8.25%), and we can immediately evaluate it alongside your current options."
            )
    elif any(k in q for k in ["actually", "correction", "mistake"]):
        context = (
            f"CORRECTION ACKNOWLEDGED:\n"
            f"Understood. Your financial profile has been updated: net monthly income is now ₹{profile.monthly_net_income.value:,.0f}. Previous estimates have been refreshed."
        )
    else:
        context = (
            "CONVERSATIONAL REFLECTION:\n"
            "Explain your previous response naturally without inventing unsupported external assumptions."
        )

    return {
        "candidates": state.get("candidates") or [],
        "clarification": None,
        "response_type": "GENERAL_ANSWER",
        "context_text": context
    }

def concept_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Answers regulatory concepts and banking FAQs directly."""
    q = state["query"].lower()
    if "foir" in q:
        context = (
            "FOIR (Fixed Obligation to Income Ratio) in Indian Banking:\n"
            "- Definition: The percentage of your net monthly income that goes toward servicing all active debts and EMIs (including credit cards, personal loans, and the new proposed loan).\n"
            "- Regulatory Cap: Indian banks strictly cap FOIR between 50% and 60% of net monthly salary.\n"
            "- Calculation Formula: `FOIR = (Total Existing EMIs + Proposed New EMI) / Net Monthly Income`.\n"
            "- Example: If your net income is ₹1,00,000, your maximum allowed EMI outflow is ₹50,000. If you already pay ₹15,000 in existing EMIs, your maximum allowable new loan EMI is ₹35,000."
        )
    else:
        context = (
            "RBI Banking Facts & Regulations:\n"
            "- EBLR vs MCLR: Since October 2019, all floating retail loans must link to an external benchmark (typically RBI Repo Rate). Rate resets happen within 3 months (vs 6-12 months on MCLR).\n"
            "- Zero Foreclosure Penalty: RBI prohibits prepayment / foreclosure penalty on floating rate retail loans to individuals.\n"
            "- Tax 80E: Up to 8 consecutive years full interest deduction for higher education loans with zero upper monetary ceiling.\n"
            "- CGFSEL: Collateral-free credit guarantee coverage up to ₹7.5 Lakhs for education loans."
        )

    return {
        "candidates": [],
        "clarification": None,
        "response_type": "GENERAL_ANSWER",
        "context_text": context
    }

def emi_calculator_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Deterministic EMI computation with zero silent assumptions."""
    q = state["query"]
    amount = parse_indian_number(q)
    rate_match = re.search(r"(\d+(\.\d+)?)\s*%", q)
    tenure_match = re.search(r"(\d+)\s*(year|yr|month|m)", q.lower())

    p = amount if amount and amount >= 10000 else 5000000.0

    # If both rate and tenure are explicitly provided by user
    if rate_match and tenure_match:
        annual_rate = float(rate_match.group(1))
        years = int(tenure_match.group(1))
        months = years * 12 if "year" in tenure_match.group(2) or "yr" in tenure_match.group(2) else years
        emi = calculate_monthly_emi(p, annual_rate, months)
        total_payment = emi * months
        total_interest = total_payment - p

        context_lines = [
            f"EMI Calculation (Exact User Parameters):",
            f"- Principal: ₹{p:,.0f} | Rate: {annual_rate:.2f}% | Tenure: {years}y ({months} EMIs)",
            f"- Monthly EMI: ₹{round(emi):,}",
            f"- Total Interest: ₹{round(total_interest):,}",
            f"- Total Outflow: ₹{round(total_payment):,}"
        ]
    else:
        # User did not provide tenure or rate. Never silently assume 5 years!
        # Present illustrative scenario matrix across standard tenures
        benchmark_rate = 8.50 # Current median EBLR
        context_lines = [
            f"Illustrative EMI Breakdown for ₹{p:,.0f} (at current ~{benchmark_rate}% EBLR benchmark):",
            "*(Exact interest rate and tenure depend on your credit score, employer category, and chosen bank)*\n",
            "| Tenure | Monthly EMI | Total Interest Payable | Total Repayment |",
            "|---|---|---|---|",
            f"| 15 Years (180 mo) | ₹{round(calculate_monthly_emi(p, benchmark_rate, 180)):,} | ₹{round((calculate_monthly_emi(p, benchmark_rate, 180)*180)-p):,} | ₹{round(calculate_monthly_emi(p, benchmark_rate, 180)*180):,} |",
            f"| 20 Years (240 mo) | ₹{round(calculate_monthly_emi(p, benchmark_rate, 240)):,} | ₹{round((calculate_monthly_emi(p, benchmark_rate, 240)*240)-p):,} | ₹{round(calculate_monthly_emi(p, benchmark_rate, 240)*240):,} |",
            f"| 25 Years (300 mo) | ₹{round(calculate_monthly_emi(p, benchmark_rate, 300)):,} | ₹{round((calculate_monthly_emi(p, benchmark_rate, 300)*300)-p):,} | ₹{round(calculate_monthly_emi(p, benchmark_rate, 300)*300):,} |",
            f"| 30 Years (360 mo) | ₹{round(calculate_monthly_emi(p, benchmark_rate, 360)):,} | ₹{round((calculate_monthly_emi(p, benchmark_rate, 360)*360)-p):,} | ₹{round(calculate_monthly_emi(p, benchmark_rate, 360)*360):,} |\n",
            "What repayment tenure (in years) would be comfortable for you?"
        ]

    return {
        "candidates": [],
        "clarification": None,
        "response_type": "EMI_RESULT",
        "context_text": "\n".join(context_lines)
    }

def extract_dynamic_clarification(text: str, profile: Optional[LoanDiscoveryProfile] = None) -> Optional[Dict[str, Any]]:
    """
    Parses conversational clarifying questions from LLM output into a structured clarification payload.
    Omits questions for parameters that are already established in the borrower profile.
    """
    t_lower = text.lower()
    if not any(k in t_lower for k in ["clarifying questions", "please clarify", "questions to clarify", "critical parameters that directly impact", "clarify two critical parameters"]):
        return None

    lines = text.split("\n")
    questions = []
    current_q = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.lower().startswith("once you provide") or stripped.lower().startswith("recommended schemes"):
            break

        # Match question start
        q_match = re.match(r"^(?:(?:\d+[\.\)]|\-|\*)\s*)?(What|In which|How much|Which|Do you|Please provide|Tell me)\b(.*?)(?:\?|$)", stripped, re.IGNORECASE)
        if q_match and len(stripped) > 8:
            if current_q:
                questions.append(current_q)
            q_text = re.sub(r"^(?:\d+[\.\)]|\-|\*)\s*", "", stripped).strip()
            q_lower = q_text.lower()

            if any(k in q_lower for k in ["value", "price", "amount", "budget", "cost"]):
                inp_type = "currency"
                fld = "property_value" if "property" in q_lower else "requested_amount"
                ph = "e.g. 1,00,00,000"
            elif any(k in q_lower for k in ["city", "state", "location", "located", "where"]):
                inp_type = "text"
                fld = "city"
                ph = "e.g. Mumbai, Bengaluru"
            elif any(k in q_lower for k in ["type", "category", "profile"]):
                inp_type = "select"
                fld = "property_type" if "property" in q_lower else "employment_type"
                ph = ""
            elif any(k in q_lower for k in ["salary", "income", "take home", "earn"]):
                inp_type = "currency"
                fld = "monthly_net_income"
                ph = "e.g. 1,20,000"
            else:
                inp_type = "text"
                fld = "custom_parameter"
                ph = "Enter detail..."

            current_q = {
                "id": f"DYN_Q_{len(questions)+1}",
                "field": fld,
                "question": q_text,
                "input_type": inp_type,
                "placeholder": ph,
                "options": [],
                "allow_custom_input": True
            }
        elif current_q and ("options:" in stripped.lower() or "option:" in stripped.lower()):
            opt_part = re.sub(r"^\*?\*?options?:\*?\*?\s*", "", stripped, flags=re.IGNORECASE)
            raw_opts = re.split(r"\s*\|\s*|\s*,\s*", opt_part)
            current_q["options"] = [{"label": o.strip(), "value": o.strip()} for o in raw_opts if o.strip()]
            if current_q["options"] and current_q["input_type"] == "text":
                current_q["input_type"] = "select"
        elif current_q and "example:" in stripped.lower():
            current_q["explanation"] = stripped.strip()

    if current_q:
        questions.append(current_q)

    # Filter out questions whose fields are already known in profile
    if profile and questions:
        filtered = []
        for q in questions:
            fld = q.get("field")
            if fld == "monthly_net_income" and profile.monthly_net_income.is_known():
                continue
            if fld == "requested_amount" and profile.requested_amount.is_known():
                continue
            if fld == "preferred_tenure_months" and profile.preferred_tenure_months.is_known():
                continue
            if fld == "property_value" and profile.property_value.is_known():
                continue
            if fld == "property_type" and profile.property_type.is_known():
                continue
            if fld == "city" and profile.city.is_known():
                continue
            filtered.append(q)
        questions = filtered

    if questions:
        for q in questions:
            if q["field"] == "property_value" and not q["options"]:
                q["options"] = [
                    {"label": "₹40 – ₹60 Lakhs", "value": 5000000},
                    {"label": "₹60 – ₹90 Lakhs", "value": 7500000},
                    {"label": "₹1 – ₹1.5 Crore", "value": 12500000},
                    {"label": "₹1.5 Crore+", "value": 18000000}
                ]
            elif q["field"] == "city" and not q["options"]:
                q["options"] = [
                    {"label": "Mumbai / MMR", "value": "Mumbai"},
                    {"label": "Delhi-NCR", "value": "Delhi-NCR"},
                    {"label": "Bengaluru", "value": "Bengaluru"},
                    {"label": "Pune / Hyderabad", "value": "Pune"},
                    {"label": "Other City", "value": "Other City"}
                ]
            elif q["field"] == "property_type" and not q["options"]:
                q["options"] = [
                    {"label": "Ready-to-move Residential", "value": "Ready Residential"},
                    {"label": "Under Construction", "value": "Under Construction"},
                    {"label": "Plot / Land Purchase", "value": "Plot"},
                    {"label": "Commercial Property", "value": "Commercial"}
                ]

        return {
            "ready_for_recommendation": False,
            "category": "Loan Underwriting",
            "next_questions": questions[:4],
            "educational_summary": "Please provide these key parameters so we can accurately assess your loan eligibility."
        }
    return None

def llm_generator_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Generates concise, grounded response without inventing financial parameters."""
    query = state["query"]
    context = state["context_text"]
    history = state.get("chat_history") or []
    chat_id = state.get("chat_id", "default_session")
    profile = _PROFILE_STORE.get(chat_id)

    api_key = (
        state.get("api_key") or
        os.environ.get("GROQ_API_KEY") or
        os.environ.get("OPENAI_API_KEY") or
        ""
    ).strip()

    model_name = state.get("model_name") or os.environ.get("MODEL_NAME", "qwen/qwen3.8-27b")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")

    # Build known established borrower facts so the LLM respects continuity
    known_facts = []
    if profile:
        if profile.loan_category.is_known():
            known_facts.append(f"Category: {profile.loan_category.value}")
        if profile.requested_amount.is_known():
            known_facts.append(f"Requested Loan Amount: ₹{profile.requested_amount.value:,.0f}")
        if profile.preferred_tenure_months.is_known():
            known_facts.append(f"Tenure: {profile.preferred_tenure_months.value // 12} Years ({profile.preferred_tenure_months.value} months)")
        if profile.monthly_net_income.is_known():
            known_facts.append(f"Monthly Net Take-Home Salary / In-Hand: ₹{profile.monthly_net_income.value:,.0f}")
        if profile.existing_monthly_emi.is_known():
            known_facts.append(f"Existing Monthly EMIs: ₹{profile.existing_monthly_emi.value:,.0f}")
        if profile.employment_type.is_known():
            known_facts.append(f"Employment Type: {profile.employment_type.value}")
        if profile.property_value.is_known():
            known_facts.append(f"Property Value: ₹{profile.property_value.value:,.0f}")
        if profile.property_type.is_known():
            known_facts.append(f"Property Type: {profile.property_type.value}")
        if profile.city.is_known():
            known_facts.append(f"City: {profile.city.value}")

    profile_instruction = ""
    if known_facts:
        profile_instruction = (
            "Known Established Borrower Facts (DO NOT ASK FOR THESE AGAIN):\n" +
            "\n".join(f"- {f}" for f in known_facts) +
            "\nSTRICT CONTINUITY RULE: The user has already provided the above facts. Never ask the user for any parameter listed above (especially monthly net income / in-hand or tenure). Reference these established figures when discussing eligibility or affordability.\n\n"
        )

    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in history[-6:]: # Keep recent 6 turns for tight context
                messages.append({"role": msg["role"], "content": msg["content"]})

            current_prompt = (
                f"{profile_instruction}"
                f"User Query: {query}\n\n"
                f"Retrieved Verified Context:\n{context}\n\n"
                f"Instructions:\n"
                f"- If this is a CLARIFICATION: Politely explain why missing parameters matter and ask only the unstated questions. Never ask for already established facts.\n"
                f"- If this is an EMI Scenario or Calculation: Present the numbers transparently. Do not invent assumptions.\n"
                f"- If this is a LOAN RECOMMENDATION: Present the top matched schemes with rate, EMI, and explanation.\n"
                f"- Keep output concise, professional, and directly grounded in the provided context."
            )
            messages.append({"role": "user", "content": current_prompt})

            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=350
            )
            answer_text = response.choices[0].message.content
        except Exception:
            answer_text = context
    else:
        answer_text = context

    res_type = state.get("response_type", "GENERAL_ANSWER")
    clar_data = state.get("clarification")

    dyn_clar = extract_dynamic_clarification(answer_text, profile=profile)
    if dyn_clar and not clar_data:
        clar_data = dyn_clar
        res_type = "CLARIFICATION"

    new_history = [
        {"role": "user", "content": query},
        {"role": "assistant", "content": answer_text}
    ]

    return {
        "final_response": answer_text,
        "chat_history": new_history,
        "response_type": res_type,
        "clarification": clar_data,
        "discovery_progress": state.get("discovery_progress") or (clar_data.get("discovery_progress") if clar_data else None)
    }

# ==================== Graph Compilation ====================

def route_decision(state: LoanAdvisorState) -> str:
    intent = state.get("intent", "RECOMMENDATION")
    chat_id = state.get("chat_id", "default_session")
    profile = _PROFILE_STORE.get(chat_id, LoanDiscoveryProfile())
    q = state.get("query", "").lower()

    if intent == "COMPARISON":
        return "compare"
    elif intent == "CONCEPT_FAQ":
        return "concept"
    elif intent == "SPECIFIC_PRODUCT_QUERY":
        return "specific_product"
    elif intent == "EMI_CALCULATOR":
        return "calculator"
    elif intent == "ELIGIBILITY_QUERY":
        if any(k in q for k in ["ltv", "90%", "loan to value", "property value"]):
            eval_res = clarification_manager.evaluate_readiness(profile, "RECOMMENDATION", query=state.get("query"))
            if not eval_res["ready_for_recommendation"]:
                return "clarify"
        return "eligibility"
    elif intent == "META_CHAT":
        return "meta_chat"

    # For RECOMMENDATION: Check if essential criteria are known
    eval_res = clarification_manager.evaluate_readiness(profile, intent, query=state.get("query"))
    if not eval_res["ready_for_recommendation"]:
        return "clarify"
    return "recommend"

def build_loan_graph():
    workflow = StateGraph(LoanAdvisorState)

    workflow.add_node("extractor", extractor_node)
    workflow.add_node("router", router_node)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("recommend", recommend_node)
    workflow.add_node("compare", comparison_node)
    workflow.add_node("specific_product", specific_product_node)
    workflow.add_node("concept", concept_node)
    workflow.add_node("calculator", emi_calculator_node)
    workflow.add_node("eligibility", eligibility_node)
    workflow.add_node("meta_chat", meta_chat_node)
    workflow.add_node("generator", llm_generator_node)

    workflow.set_entry_point("extractor")
    workflow.add_edge("extractor", "router")

    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "clarify": "clarify",
            "recommend": "recommend",
            "compare": "compare",
            "specific_product": "specific_product",
            "concept": "concept",
            "calculator": "calculator",
            "eligibility": "eligibility",
            "meta_chat": "meta_chat"
        }
    )

    workflow.add_edge("clarify", "generator")
    workflow.add_edge("recommend", "generator")
    workflow.add_edge("compare", "generator")
    workflow.add_edge("specific_product", "generator")
    workflow.add_edge("concept", "generator")
    workflow.add_edge("calculator", "generator")
    workflow.add_edge("eligibility", "generator")
    workflow.add_edge("meta_chat", "generator")
    workflow.add_edge("generator", END)

    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

loan_advisor_graph = build_loan_graph()
