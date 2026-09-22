import os
import re
import json
import operator
from typing import TypedDict, List, Dict, Optional, Any, Annotated
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from rag.engine import LoanRecommendationEngine
from rag.router import semantic_router
from rag.policies import CATEGORY_POLICIES

MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "catalog_manifest.json")

# State schema for LangGraph with append-only chat history & session tracking
class LoanAdvisorState(TypedDict):
    chat_id: str
    query: str
    user_profile: Dict[str, Any]
    intent: str
    active_category: Optional[str]
    monthly_income_num: Optional[float]
    candidates: List[Dict[str, Any]]
    active_schemes: List[Dict[str, Any]]  # Stores active schemes from previous turns
    comparison_schemes: List[Dict[str, Any]]
    emi_result: Optional[Dict[str, Any]]
    context_text: str
    chat_history: Annotated[List[Dict[str, str]], operator.add]  # Stateful conversation memory
    final_response: str
    api_key: Optional[str]
    model_name: Optional[str]

# Load manifest for exact entity lookup
with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    ALL_SCHEMES = json.load(f)["schemes"]

engine = LoanRecommendationEngine()

# Ultra-concise, token-efficient system instruction
SYSTEM_PROMPT = """You are FinNav, an expert, concise Indian Retail Loan Advisor.
CORE RULES:
1. Conversation Context: Maintain strict continuity across turns. Refer back to discussed categories, income levels, and schemes naturally.
2. Ultra-Concise: Provide 2-4 clean, direct bullet points (under 130 words). No verbose filler greetings.
3. Ineligibility Reality: If an applicant's income is below the minimum threshold for standard loans (e.g., Rs. 10,000/month for home loans), DO NOT recommend or suggest ineligible commercial bank loans. Instead, clearly explain why they are ineligible and outline practical alternatives (e.g. adding an earning co-applicant, exploring PMAY or micro-housing NBFCs, saving a higher down payment).
4. Informational & Follow-up Inquiries: When the user asks about eligibility criteria, monthly income benchmarks, documents, or banking rules (without asking to find or recommend a loan), answer the question directly and factually. DO NOT push unrequested loan recommendations, and DO NOT output key signatures.
5. Product Recommendations (Eligible Only): When the applicant qualifies and explicitly seeks recommendations, list: Scheme Name, Bank, Key Signature (`rate_sector_tenure_category`), Rate, Tenure, and Official Link.
6. Comparisons: Provide a compact 3-row markdown table (Rate, Tenure, Fee/LTV).
7. Absolute Accuracy: Rely EXCLUSIVELY on the verified context provided. Never invent rates, numbers, or terms.
"""

def parse_monthly_income(query: str, profile_income: str = None) -> Optional[float]:
    """Extracts net monthly income in Rupees from query or user profile."""
    # 1. First priority: Check query text
    q = (query or "").lower().replace(",", "").replace("₹", "").replace("rs.", "").strip()

    m_match = re.search(r"(?:monthly|salary|per\s*month|pm|p\.m\.|earning)\s*(?:of|is|:)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac|l)?", q)
    if m_match:
        val = float(m_match.group(1))
        unit = m_match.group(2)
        if unit in ["k", "thousand"]:
            return val * 1000
        elif unit in ["lakh", "lac", "l"]:
            return val * 100000
        elif val < 500:
            return val * 1000 if val <= 100 else val
        return val

    inc_match = re.search(r"income\s*(?:of|is|:)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac|l)?", q)
    if inc_match:
        val = float(inc_match.group(1))
        unit = inc_match.group(2)
        if unit in ["k", "thousand"]:
            return val * 1000
        elif unit in ["lakh", "lac", "l"]:
            return val * 100000
        return val * 1000 if val <= 100 else val

    # 2. Second priority: Profile input
    p = (profile_income or "").lower().replace(",", "").replace("₹", "").replace("rs.", "").strip()
    if p:
        is_annual = any(w in p for w in ["annual", "ctc", "pa", "p.a."])
        m2 = re.search(r"(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac|l|cr)?", p)
        if m2:
            val = float(m2.group(1))
            unit = m2.group(2)
            if unit in ["k", "thousand"]:
                amt = val * 1000
            elif unit in ["lakh", "lac", "l"]:
                amt = val * 100000
            elif unit == "cr":
                amt = val * 10000000
            elif val > 1000:
                amt = val
            else:
                amt = val * 1000

            if is_annual or amt >= 1000000:
                return amt / 12.0
            return amt

    return None

def extract_loan_amount(query: str, profile_amt: str = None) -> Optional[float]:
    """Extracts requested loan amount in Lakhs, ignoring income/salary figures."""
    p = (profile_amt or "").lower().replace(",", "").replace("₹", "").replace("rs.", "").strip()
    if p:
        cr_m = re.search(r"(\d+(?:\.\d+)?)\s*(cr|crore)", p)
        if cr_m:
            return float(cr_m.group(1)) * 100.0
        l_m = re.search(r"(\d+(?:\.\d+)?)\s*(lakh|lac|l)", p)
        if l_m:
            return float(l_m.group(1))
        k_m = re.search(r"(\d+(?:\.\d+)?)\s*(k|thousand)", p)
        if k_m:
            return float(k_m.group(1)) * 0.01
        num_m = re.search(r"(\d+(?:\.\d+)?)", p)
        if num_m:
            val = float(num_m.group(1))
            return val / 100000.0 if val > 10000 else val

    # Query text (stripping income mentions first)
    q = (query or "").lower().replace(",", "").replace("₹", "").replace("rs.", "").strip()
    cleaned = re.sub(r"(?:monthly|salary|income|earning|ctc)\s*(?:of|is|:)?\s*\d+(?:\.\d+)?\s*(?:k|thousand|lakh|lac|l|cr|crore)?", "", q)

    cr_m = re.search(r"(\d+(?:\.\d+)?)\s*(cr|crore)", cleaned)
    if cr_m:
        return float(cr_m.group(1)) * 100.0
    l_m = re.search(r"(\d+(?:\.\d+)?)\s*(lakh|lac|l)", cleaned)
    if l_m:
        return float(l_m.group(1))
    return None

def router_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Routes query to specialized intent using local vector semantic router."""
    intent = semantic_router.route(state["query"])
    return {"intent": intent}

def comparison_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Splits comparative query into entities and retrieves exact verified cards for both sides."""
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
        category_filter = state["user_profile"].get("Category Filter") or state.get("active_category")
        semantic_candidates = engine.retrieve(query=state["query"], category=category_filter, section_type="parent_card", n_results=2)
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
        "context_text": "\n".join(context_lines)
    }

def eligibility_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Answers eligibility, income norms, criteria, and documentation questions using declarative policies."""
    q = state["query"].lower().strip()
    profile = state.get("user_profile") or {}

    # Resolve category from query or active category in state
    category = None
    if any(w in q for w in ["home loan", "homeloan", "housing"]):
        category = "Home Loan"
    elif any(w in q for w in ["personal loan", "personalloan"]):
        category = "Personal Loan"
    elif any(w in q for w in ["education loan", "student loan", "study"]):
        category = "Education Loan"
    elif any(w in q for w in ["car loan", "auto loan", "vehicle loan"]):
        category = "Vehicle Loan"
    else:
        category = state.get("active_category") or profile.get("Category Filter") or "Home Loan"

    policy = CATEGORY_POLICIES.get(category, CATEGORY_POLICIES["Home Loan"])
    monthly_income = parse_monthly_income(q, profile.get("Income")) or state.get("monthly_income_num")

    # 1. Anaphoric / Contextual Check on Active Schemes ("these banks", "them", "both", "it")
    active_schemes = state.get("active_schemes") or []
    is_referring_to_active = any(b in q for b in ["these banks", "these loans", "these schemes", "these options", "these", "them", "both", "from them", "the first one", "the second one", "it", "this"])

    if active_schemes and is_referring_to_active:
        scheme_blocks = []
        for idx, s in enumerate(active_schemes, 1):
            m = s["metadata"]
            s_name = m.get("scheme_name")
            s_inst = m.get("institution")
            # Retrieve verified eligibility specifics for this exact scheme
            el_docs = engine.retrieve(query=f"{s_name} eligibility", section_type="eligibility", n_results=1)
            el_text = el_docs[0]["document"].split("Details:\n")[-1].strip() if el_docs else "Standard norms apply."
            scheme_blocks.append(
                f"[{idx}] {s_name} ({s_inst}):\n"
                f"- Key: `{m.get('compact_key')}`\n"
                f"- Eligibility Criteria: {el_text[:350]}\n"
                f"- Portal: {m.get('source_url')}"
            )

        income_display = f"Rs. {int(monthly_income):,}/month" if monthly_income else "your declared income"
        context = (
            f"Verified Eligibility Assessment for Currently Active Schemes:\n"
            f"Applicant Declared Monthly Income: {income_display}\n\n"
            + "\n\n".join(scheme_blocks) + "\n\n"
            f"CRITICAL INSTRUCTIONS FOR LLM:\n"
            f"1. Directly evaluate whether the applicant can get a loan from THESE SPECIFIC active schemes ({', '.join([s['metadata']['institution'] for s in active_schemes])}) based on their income.\n"
            f"2. Confirm that affordable housing schemes (like Union Awas and YES Khushi) have lower income thresholds (starting at Rs. 9,000–12,000) and the applicant DOES qualify for them.\n"
            f"3. Do NOT mention or introduce any other unretrieved banks (such as Bank of India, Bank of Baroda, etc.)."
        )
        return {
            "candidates": active_schemes,
            "active_category": category,
            "context_text": context
        }

    # 2. General Documentation Queries
    if any(k in q for k in ["document", "paper", "proof", "kyc"]):
        context = (
            f"Mandatory Documents Required for {category}:\n"
            "- Identity & Address Proof: PAN Card (mandatory), Aadhaar Card, Passport, or Voter ID.\n"
            "- Income Proof (Salaried): Last 3 months salary slips, 6 months bank statements showing salary credit, Form 16 / ITR.\n"
            "- Income Proof (Self-Employed): Last 2-3 years audited balance sheets, P&L, ITR with computation of income, 6 months business bank statement.\n"
            "- Property/Collateral Documents (if Home/Vehicle): Title deeds, NOC from builder/society, approved building plan, sale agreement."
        )
    # 3. Generic Income Benchmark Queries
    elif any(k in q for k in ["generic", "most of", "industry", "average", "typical"]) or "monthly income" in q or "salary" in q:
        if category == "Home Loan":
            context = (
                "Verified Indian Home Loan Monthly Income Eligibility Standards:\n"
                f"- Public Sector Banks (SBI, Bank of Baroda, PNB): Minimum Rs. {policy['standard_min_income'] - 5000:,} to Rs. {policy['standard_min_income']:,} net monthly salary.\n"
                f"- Private Sector Banks (HDFC, ICICI, Kotak, Federal Bank): Minimum Rs. {policy['standard_min_income']:,} (Tier-2/3) to Rs. {policy['metro_min_income']:,}/month (Tier-1/Metros).\n"
                f"- Affordable Housing Finance (Kotak Vishwas, PMAY-aligned HFCs): Minimum Rs. 10,000 to Rs. {policy['min_individual_income']:,}/month.\n"
                f"- FOIR (Fixed Obligation to Income Ratio): All banks cap total monthly debt obligations at {int(policy['max_foir']*100)}% of net monthly income.\n"
                f"- Age & Stability: {policy['min_age']}-{policy['max_age']} years of age; minimum 2 years continuous employment stability."
            )
        else:
            context = (
                f"Verified Standards for {category}:\n"
                f"- Minimum Net Monthly Income: Rs. {policy.get('min_individual_income', 15000):,} (entry) to Rs. {policy.get('standard_min_income', 25000):,} (prime lenders).\n"
                f"- Age Window: {policy.get('min_age', 21)} to {policy.get('max_age', 65)} years.\n"
                f"- Credit Track Record: CIBIL {policy.get('min_cibil', 700)}+.\n"
                f"- Maximum Debt Burden (FOIR): {int(policy.get('max_foir', 0.5)*100)}% of monthly take-home pay."
            )
    else:
        context = (
            f"Standard Minimum Eligibility Criteria for {category} across Indian Banks:\n"
            f"- Net Monthly Income: Rs. {policy.get('min_individual_income', 12000):,} (affordable schemes) to Rs. {policy.get('standard_min_income', 20000):,} - Rs. {policy.get('metro_min_income', 25000):,}/month (standard commercial banks).\n"
            f"- Age Window: {policy.get('min_age', 18)} to {policy.get('max_age', 70)} years at loan maturity.\n"
            f"- Employment Stability: Minimum 2 years continuous work experience (or 3 years business continuity for self-employed).\n"
            f"- Credit Score: Minimum CIBIL score of {policy.get('min_cibil', 700)}+ (750+ needed for lowest interest rate tier).\n"
            f"- FOIR Ceiling: Monthly EMIs cannot exceed {int(policy.get('max_foir', 0.5)*100)}% of net monthly take-home pay."
        )

    return {
        "candidates": [],
        "active_category": category,
        "context_text": context
    }

def meta_chat_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Answers conversational reflections, explanations, and meta-dialogue directly from history."""
    active_schemes = state.get("active_schemes") or []
    scheme_names = [f"{s['metadata']['scheme_name']} ({s['metadata']['institution']})" for s in active_schemes]
    schemes_str = ", ".join(scheme_names) if scheme_names else "the previously discussed schemes"

    context = (
        "CONVERSATIONAL REFLECTION & CLARIFICATION:\n"
        f"The user is asking a conversational question or clarification regarding your previous responses about {schemes_str}.\n\n"
        "CRITICAL INSTRUCTIONS FOR LLM:\n"
        "1. Rely EXCLUSIVELY on your previous conversational messages to explain your rationale.\n"
        "2. Do NOT run external database searches and do NOT mention any unretrieved banks.\n"
        "3. Explain clearly that you suggested these schemes because they are affordable housing products with lower income thresholds (starting at Rs. 9,000–12,000/month) tailored for their declared income, unlike standard prime loans which require Rs. 20,000+."
    )
    return {
        "candidates": active_schemes,
        "active_category": state.get("active_category") or "Home Loan",
        "context_text": context
    }

def recommend_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Retrieves candidates using section-aware matching, amount bounds, income eligibility, and category detection."""
    q = state["query"].lower().strip()
    profile = state.get("user_profile") or {}
    category = profile.get("Category Filter") or state.get("active_category")
    sector = profile.get("Sector Filter")

    # Detect category from query if specified by user (e.g. 'i meant for homeloan')
    if any(w in q for w in ["home loan", "homeloan", "housing", "mortgage"]):
        category = "Home Loan"
    elif any(w in q for w in ["personal loan", "personalloan"]):
        category = "Personal Loan"
    elif any(w in q for w in ["education loan", "study loan", "student loan", "scholar"]):
        category = "Education Loan"
    elif any(w in q for w in ["car loan", "auto loan", "vehicle loan", "two wheeler"]):
        category = "Vehicle Loan"
    elif not category:
        category = "Home Loan"

    policy = CATEGORY_POLICIES.get(category, CATEGORY_POLICIES["Home Loan"])

    # Parse requested loan amount in Lakhs (e.g. 2cr -> 200.0 Lakhs)
    raw_amt = profile.get("Requested Amount") or ""
    amt_lakhs = extract_loan_amount(q, raw_amt)

    # Monthly income extraction
    monthly_income = parse_monthly_income(q, profile.get("Income"))
    if not monthly_income and state.get("monthly_income_num"):
        monthly_income = state.get("monthly_income_num")

    # Declarative minimum income eligibility pre-check:
    min_income_floor = policy.get("min_individual_income", 0)
    if monthly_income is not None and min_income_floor > 0 and monthly_income < min_income_floor:
        advisory_context = (
            f"ELIGIBILITY ADVISORY (Income Below Qualification Threshold):\n"
            f"- Applicant Net Monthly Income: Rs. {int(monthly_income):,}/month.\n"
            f"- Minimum Norms for {category}:\n{policy.get('guidance', '')}\n"
            f"- Reason for Ineligibility: With Rs. {int(monthly_income):,}/month, regulatory FOIR ({int(policy.get('max_foir', 0.5)*100)}%) caps allowable monthly EMI, which cannot service individual standard {category.lower()} amounts.\n\n"
            f"CRITICAL INSTRUCTION: State clearly that a monthly income of Rs. {int(monthly_income):,} is below the minimum eligibility threshold for standard {category.lower()}s. Present the practical alternatives (co-applicant, government/affordable schemes, down payment). DO NOT recommend any prime loan schemes and DO NOT output key signatures."
        )
        return {
            "candidates": [],
            "active_category": category,
            "monthly_income_num": monthly_income,
            "context_text": advisory_context
        }

    # Contextual Follow-up Resolution (Pronoun & Index resolution)
    active_schemes = state.get("active_schemes") or []
    target_scheme_name = None

    if active_schemes:
        if any(p in q for p in ["first", "1st"]):
            target_scheme_name = active_schemes[0]["metadata"]["scheme_name"]
        elif any(p in q for p in ["second", "2nd"]) and len(active_schemes) >= 2:
            target_scheme_name = active_schemes[1]["metadata"]["scheme_name"]
        elif any(p in q for p in ["it", "this", "that", "the loan", "for this"]):
            target_scheme_name = active_schemes[0]["metadata"]["scheme_name"]

    target_section = "parent_card"
    if any(k in q for k in ["document", "paper", "proof", "kyc", "itr", "salary slip"]):
        target_section = "documents"
    elif any(k in q for k in ["foreclos", "prepay", "penalty", "charge", "fee"]):
        target_section = "fees"
    elif any(k in q for k in ["benchmark", "eblr", "mclr", "spread"]):
        target_section = "rates"

    search_query = f"{target_scheme_name} {q}" if target_scheme_name else state["query"]

    candidates = engine.retrieve(
        query=search_query,
        category=category,
        sector=sector,
        section_type=target_section,
        loan_amount_lakhs=amt_lakhs,
        n_results=2
    )

    if not candidates:
        candidates = engine.retrieve(
            query=search_query,
            category=category,
            sector=sector,
            section_type="parent_card",
            loan_amount_lakhs=amt_lakhs,
            n_results=2
        )

    context_blocks = []
    for idx, c in enumerate(candidates, 1):
        m = c["metadata"]
        key = m.get("compact_key", f"{m.get('interest_rate_range')}_{m.get('sector')}_{m.get('max_tenure_years')}y_{m.get('category')}")
        sec_type = m.get("section_type", "summary")

        card = (
            f"[{idx}] {m.get('scheme_name')} ({m.get('institution')}) | Section: {sec_type.upper()}\n"
            f"- Key: `{key}`\n"
            f"- Rate: {m.get('interest_rate_range')} ({m.get('benchmark')})\n"
            f"- Max: {m.get('max_loan_amount')}, {m.get('max_tenure_years')}y\n"
            f"- Link: {m.get('source_url')}"
        )

        if target_section != "parent_card" and "document" in c:
            clean_text = c["document"].split("Details:\n")[-1].strip()
            card += f"\n- {sec_type.capitalize()} Specifics: {clean_text[:300]}"

        context_blocks.append(card)

    return {
        "candidates": candidates,
        "active_category": category,
        "monthly_income_num": monthly_income,
        "active_schemes": candidates if target_section == "parent_card" else active_schemes,
        "context_text": "\n\n".join(context_blocks)
    }

def concept_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Concise Indian banking and regulatory facts (under 75 tokens)."""
    concept_context = (
        "RBI Banking Facts:\n"
        "- EBLR vs MCLR: Since Oct 2019, all floating retail loans must link to external benchmark (Repo rate). Reset occurs within 3 months (vs 6-12 months on MCLR).\n"
        "- Prepayment: RBI prohibits foreclosure/prepayment penalties on floating rate retail loans to individuals.\n"
        "- Tax 80E: Up to 8 years full interest deduction for higher education loans with zero upper cap.\n"
        "- CGFSEL: Collateral-free credit guarantee up to Rs. 7.5L for education loans."
    )
    return {
        "candidates": [],
        "context_text": concept_context
    }

def emi_calculator_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Deterministic, zero-token-waste math computation."""
    q = state["query"]
    amount_match = re.search(r"(\d+(\.\d+)?)\s*(lakh|lac|l|crore|cr|k)?", q.lower())
    rate_match = re.search(r"(\d+(\.\d+)?)\s*%", q)
    tenure_match = re.search(r"(\d+)\s*(year|yr|month|m)", q.lower())

    p = 1000000.0
    if amount_match:
        val = float(amount_match.group(1))
        unit = amount_match.group(3)
        if unit in ["lakh", "lac", "l"]:
            p = val * 100000
        elif unit in ["crore", "cr"]:
            p = val * 10000000
        elif unit == "k":
            p = val * 1000
        elif val > 10000:
            p = val

    r_annual = float(rate_match.group(1)) if rate_match else 8.75
    t_years = int(tenure_match.group(1)) if tenure_match else 5

    monthly_r = (r_annual / 12) / 100
    n = t_years * 12
    emi = p * monthly_r * ((1 + monthly_r)**n) / (((1 + monthly_r)**n) - 1)
    total_payment = emi * n
    total_interest = total_payment - p

    context_lines = [
        f"EMI Calculation (Exact Math):",
        f"- Principal: Rs. {p:,.0f} | Rate: {r_annual:.2f}% | Tenure: {t_years}y ({n} EMIs)",
        f"- Monthly EMI: Rs. {round(emi):,}",
        f"- Total Interest: Rs. {round(total_interest):,}",
        f"- Total Outflow: Rs. {round(total_payment):,}"
    ]

    return {
        "candidates": [],
        "context_text": "\n".join(context_lines)
    }

def llm_generator_node(state: LoanAdvisorState) -> Dict[str, Any]:
    """Generates concise response maintaining full conversation history."""
    query = state["query"]
    context = state["context_text"]
    history = state.get("chat_history") or []

    api_key = (
        state.get("api_key") or
        os.environ.get("GROQ_API_KEY") or
        os.environ.get("OPENAI_API_KEY") or
        ""
    ).strip()

    model_name = state.get("model_name") or os.environ.get("MODEL_NAME", "qwen/qwen3.8-27b")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")

    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)

            # Build multi-turn messages array preserving past turns
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Add past conversational history
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})

            # Add current user prompt with grounded context
            current_prompt = (
                f"User Question: {query}\n"
                f"Retrieved Verified Context:\n{context}\n\n"
                f"Guidelines:\n"
                f"- If this is an Eligibility Advisory or General Criteria answer: Answer directly in 2-3 concise bullet points. DO NOT recommend prime loan schemes and DO NOT output key signatures.\n"
                f"- If this is a valid Loan Recommendation: Provide candidate schemes with Name, Bank, Key Signature (`rate_sector_tenure_category`), Rate, Tenure, and Link.\n"
                f"- If this is a Comparison: Provide a compact 3-row markdown table.\n"
                f"- Maintain conversation continuity across turns."
            )
            messages.append({"role": "user", "content": current_prompt})

            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=250
            )
            answer_text = response.choices[0].message.content
        except Exception as e:
            answer_text = f"*(Note: LLM provider unavailable. Returning instant verified catalog data directly)*\n\n{context}"
    else:
        answer_text = context

    new_history_entries = [
        {"role": "user", "content": query},
        {"role": "assistant", "content": answer_text}
    ]

    return {
        "final_response": answer_text,
        "chat_history": new_history_entries
    }

# Compile Workflow with Checkpointer for session persistence
def build_loan_graph():
    workflow = StateGraph(LoanAdvisorState)

    workflow.add_node("router", router_node)
    workflow.add_node("recommend", recommend_node)
    workflow.add_node("compare", comparison_node)
    workflow.add_node("concept", concept_node)
    workflow.add_node("calculator", emi_calculator_node)
    workflow.add_node("eligibility", eligibility_node)
    workflow.add_node("meta_chat", meta_chat_node)
    workflow.add_node("generator", llm_generator_node)

    workflow.set_entry_point("router")

    def route_decision(state: LoanAdvisorState):
        intent = state.get("intent", "RECOMMENDATION")
        if intent == "COMPARISON":
            return "compare"
        elif intent == "CONCEPT_FAQ":
            return "concept"
        elif intent == "EMI_CALCULATOR":
            return "calculator"
        elif intent == "ELIGIBILITY_QUERY":
            return "eligibility"
        elif intent == "META_CHAT":
            return "meta_chat"
        return "recommend"

    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "compare": "compare",
            "concept": "concept",
            "calculator": "calculator",
            "eligibility": "eligibility",
            "meta_chat": "meta_chat",
            "recommend": "recommend"
        }
    )

    workflow.add_edge("compare", "generator")
    workflow.add_edge("concept", "generator")
    workflow.add_edge("calculator", "generator")
    workflow.add_edge("eligibility", "generator")
    workflow.add_edge("meta_chat", "generator")
    workflow.add_edge("recommend", "generator")
    workflow.add_edge("generator", END)

    # Use MemorySaver checkpointer for thread/chat persistence
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

loan_advisor_graph = build_loan_graph()
