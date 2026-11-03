from typing import List, Dict, Any, Optional
from rag.discovery import LoanDiscoveryProfile, LoanCategory, FieldState

QUESTION_BANK: Dict[str, Dict[str, Any]] = {
    "HOME_LOAN_AMOUNT": {
        "id": "HOME_LOAN_AMOUNT",
        "field": "requested_amount",
        "question": "What is your approximate required home loan quantum?",
        "explanation": "RBI sets Loan-To-Value (LTV) limits: up to 90% for loans under ₹30 Lakhs, 80% up to ₹75 Lakhs, and 75% above ₹75 Lakhs.",
        "input_type": "currency",
        "placeholder": "e.g. 60,00,000 or 1.2 Crore",
        "options": [
            {"label": "₹25 – ₹40 Lakhs", "value": 3500000},
            {"label": "₹50 – ₹75 Lakhs", "value": 6000000},
            {"label": "₹75 Lakhs – ₹1.2 Cr", "value": 9000000},
            {"label": "₹1.5 Crore+", "value": 15000000}
        ],
        "allow_custom_input": True
    },
    "HOME_LOAN_TENURE": {
        "id": "HOME_LOAN_TENURE",
        "field": "preferred_tenure_months",
        "question": "What repayment tenure are you considering?",
        "explanation": "Tenure determines your monthly EMI and total interest outflow. Longer tenures lower your monthly installment but increase cumulative interest.",
        "input_type": "select",
        "options": [
            {"label": "15 Years (180 mo)", "value": 180},
            {"label": "20 Years (240 mo)", "value": 240},
            {"label": "25 Years (300 mo)", "value": 300},
            {"label": "30 Years (360 mo)", "value": 360}
        ],
        "allow_custom_input": False
    },
    "MONTHLY_NET_INCOME": {
        "id": "MONTHLY_NET_INCOME",
        "field": "monthly_net_income",
        "question": "What is your net monthly take-home salary or income?",
        "explanation": "Banks verify that your total EMIs do not exceed 50% to 60% of your take-home pay under RBI FOIR guidelines.",
        "input_type": "currency",
        "placeholder": "e.g. 1,20,000",
        "options": [
            {"label": "₹35,000 – ₹60,000", "value": 50000},
            {"label": "₹60,000 – ₹1 Lakh", "value": 80000},
            {"label": "₹1 Lakh – ₹1.8 Lakhs", "value": 140000},
            {"label": "₹2 Lakhs+", "value": 250000}
        ],
        "allow_custom_input": True
    },
    "PROPERTY_VALUE": {
        "id": "PROPERTY_VALUE",
        "field": "property_value",
        "question": "What is the total property value / purchase price?",
        "explanation": "Banks lend 90% only up to ₹30 Lakhs, 80% up to ₹75 Lakhs, and 75% above ₹75 Lakhs based on registered value or valuer appraisal.",
        "input_type": "currency",
        "placeholder": "e.g. 1,00,00,000 or 85 Lakhs",
        "options": [
            {"label": "₹30 – ₹50 Lakhs", "value": 4000000},
            {"label": "₹50 – ₹75 Lakhs", "value": 6500000},
            {"label": "₹75 Lakhs – ₹1.2 Cr", "value": 9500000},
            {"label": "₹1.5 Crore+", "value": 18000000}
        ],
        "allow_custom_input": True
    },
    "PROPERTY_TYPE": {
        "id": "PROPERTY_TYPE",
        "field": "property_type",
        "question": "What is the property type?",
        "explanation": "Standard 90% LTV applies to residential apartments/villas. Commercial properties and land/plots are capped at 60%–70% LTV.",
        "input_type": "select",
        "options": [
            {"label": "Ready-to-move Residential", "value": "Ready Residential"},
            {"label": "Under Construction", "value": "Under Construction"},
            {"label": "Plot / Land Purchase", "value": "Plot"},
            {"label": "Commercial Property", "value": "Commercial"}
        ],
        "allow_custom_input": False
    },
    "PROPERTY_LOCATION": {
        "id": "PROPERTY_LOCATION",
        "field": "city",
        "question": "In which city/state is the property located?",
        "explanation": "Tier-1 metro properties support higher bank valuation clearance and lower margin haircut than peripheral zones.",
        "input_type": "text",
        "placeholder": "e.g. Mumbai, Bengaluru, Pune",
        "options": [
            {"label": "Mumbai / MMR", "value": "Mumbai"},
            {"label": "Delhi-NCR", "value": "Delhi-NCR"},
            {"label": "Bengaluru", "value": "Bengaluru"},
            {"label": "Pune / Hyderabad", "value": "Pune"},
            {"label": "Tier-2 / Other", "value": "Other City"}
        ],
        "allow_custom_input": True
    },
    "EMPLOYMENT_TYPE": {
        "id": "EMPLOYMENT_TYPE",
        "field": "employment_type",
        "question": "What is your employment profile?",
        "explanation": "Salaried corporate employees often qualify for special discounted EBLR interest rate spreads and waived processing fees.",
        "input_type": "select",
        "options": [
            {"label": "Salaried (MNC / Listed / Govt)", "value": "Salaried"},
            {"label": "Self-Employed Business / Proprietor", "value": "Self-Employed"},
            {"label": "Professional (Doctor / CA / Architect)", "value": "Self-Employed Professional"}
        ],
        "allow_custom_input": False
    },
    "EXISTING_MONTHLY_EMI": {
        "id": "EXISTING_MONTHLY_EMI",
        "field": "existing_monthly_emi",
        "question": "Approximately what are your existing monthly EMI commitments?",
        "explanation": "Every ₹10,000 of active loan EMIs reduces your new loan eligibility by approximately ₹8 to ₹10 Lakhs.",
        "input_type": "currency",
        "placeholder": "e.g. 15,000 (or 0)",
        "options": [
            {"label": "Zero / No existing EMIs", "value": 0},
            {"label": "Under ₹15,000 / month", "value": 10000},
            {"label": "₹15,000 – ₹30,000 / month", "value": 22000},
            {"label": "₹30,000+ / month", "value": 45000}
        ],
        "allow_custom_input": True
    },
    "CIBIL_SCORE_TIER": {
        "id": "CIBIL_SCORE_TIER",
        "field": "self_reported_credit_score",
        "question": "Do you know your approximate CIBIL credit score?",
        "explanation": "RBI mandates risk-tiered interest pricing: scores of 750+ unlock prime rates with zero bank spread markup.",
        "input_type": "number",
        "placeholder": "e.g. 780",
        "options": [
            {"label": "Excellent (750+)", "value": 780},
            {"label": "Good (700 – 749)", "value": 725},
            {"label": "Fair / Under 700", "value": 670},
            {"label": "Not Sure / Don't Know", "value": -1}
        ],
        "allow_custom_input": True
    },
    "BORROWER_PRIORITY": {
        "id": "BORROWER_PRIORITY",
        "field": "priorities",
        "question": "What matters most to you in this loan?",
        "explanation": "We use your priority to rank products that minimize overall interest expense versus those that minimize monthly cash outflow.",
        "input_type": "select",
        "options": [
            {"label": "Lowest Total Interest Cost", "value": "LOWEST_TOTAL_INTEREST"},
            {"label": "Lowest Monthly Installment (EMI)", "value": "LOWER_MONTHLY_EMI"},
            {"label": "Minimal Processing Fees & Charges", "value": "LOW_FEES"},
            {"label": "Fastest Sanction & Approval", "value": "FAST_PROCESSING"}
        ],
        "allow_custom_input": False
    }
}

class ClarificationManager:
    """
    Evaluates whether the profile has sufficient underwriting parameters to recommend loans,
    or whether targeted clarification questions must be asked first.
    """

    def evaluate_readiness(
        self,
        profile: LoanDiscoveryProfile,
        intent: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determines whether the engine is ready to generate personalized recommendations,
        or what questions to ask next. Supports LTV-specific underwriting requests.
        """
        # Non-discovery intents don't need discovery clarification
        if intent in ["GENERAL_EDUCATION", "CONCEPT_FAQ", "SPECIFIC_PRODUCT_QUERY"]:
            return {
                "ready_for_recommendation": True,
                "missing_critical_fields": [],
                "next_questions": []
            }

        q_lower = (query or "").lower()
        is_ltv_query = any(k in q_lower for k in ["ltv", "loan to value", "property value", "purchase price", "margin money", "down payment"])

        missing_critical = []
        missing_important = []

        if is_ltv_query:
            # For LTV inquiries, property valuation and property type dictate the allowable LTV ceiling
            if not profile.property_value.is_known():
                missing_critical.append("property_value")
            if not profile.property_type.is_known():
                missing_critical.append("property_type")
            if not profile.city.is_known():
                missing_important.append("city")
            if not profile.monthly_net_income.is_known():
                missing_important.append("monthly_net_income")

            ready = len(missing_critical) == 0

            next_question_keys = []
            if "property_value" in missing_critical:
                next_question_keys.append("PROPERTY_VALUE")
            if "property_type" in missing_critical:
                next_question_keys.append("PROPERTY_TYPE")
            if not profile.city.is_known():
                next_question_keys.append("PROPERTY_LOCATION")
            if len(next_question_keys) < 3 and "monthly_net_income" in missing_important:
                next_question_keys.append("MONTHLY_NET_INCOME")

            selected_questions = [QUESTION_BANK[k] for k in next_question_keys[:3] if k in QUESTION_BANK]

            return {
                "ready_for_recommendation": ready,
                "category": f"{profile.loan_category.value or 'Home Loan'} LTV",
                "completion_level": "COMPLETE" if ready and len(missing_important) == 0 else ("PARTIAL" if ready else "INSUFFICIENT"),
                "missing_critical_fields": missing_critical,
                "missing_important_fields": missing_important,
                "next_questions": selected_questions,
                "educational_summary": (
                    "To accurately assess your eligibility for a 90% Loan-to-Value (LTV) request under RBI guidelines, "
                    "banks lend up to 90% only for loans up to ₹30 Lakhs, 80% up to ₹75 Lakhs, and 75% above ₹75 Lakhs "
                    "for residential properties. Commercial properties and plots are capped at 60%–70% LTV."
                )
            }

        # Standard discovery: Critical: Amount, Income, Tenure
        if not profile.requested_amount.is_known():
            missing_critical.append("requested_amount")
        if not profile.monthly_net_income.is_known():
            missing_critical.append("monthly_net_income")
        if not profile.preferred_tenure_months.is_known():
            missing_critical.append("preferred_tenure_months")

        # Important: Existing EMIs, Employment Type
        if not profile.existing_monthly_emi.is_known():
            missing_important.append("existing_monthly_emi")
        if not profile.employment_type.is_known():
            missing_important.append("employment_type")

        # Ready if all critical fields are known
        ready = len(missing_critical) == 0

        # Prioritize 2-3 questions for next turn
        next_question_keys = []
        if "requested_amount" in missing_critical:
            next_question_keys.append("HOME_LOAN_AMOUNT")
        if "preferred_tenure_months" in missing_critical:
            next_question_keys.append("HOME_LOAN_TENURE")
        if "monthly_net_income" in missing_critical:
            next_question_keys.append("MONTHLY_NET_INCOME")

        if len(next_question_keys) < 2 and "existing_monthly_emi" in missing_important:
            next_question_keys.append("EXISTING_MONTHLY_EMI")
        if len(next_question_keys) < 2 and "employment_type" in missing_important:
            next_question_keys.append("EMPLOYMENT_TYPE")
        if len(next_question_keys) < 3 and not profile.self_reported_credit_score.is_known() and profile.self_reported_credit_score.state != FieldState.DECLINED:
            next_question_keys.append("CIBIL_SCORE_TIER")

        selected_questions = [QUESTION_BANK[k] for k in next_question_keys[:3] if k in QUESTION_BANK]

        return {
            "ready_for_recommendation": ready,
            "category": profile.loan_category.value or "Loan",
            "completion_level": "COMPLETE" if ready and len(missing_important) == 0 else ("PARTIAL" if ready else "INSUFFICIENT"),
            "missing_critical_fields": missing_critical,
            "missing_important_fields": missing_important,
            "next_questions": selected_questions,
            "educational_summary": (
                f"To identify the most competitive, verified {profile.loan_category.value or 'loan'} options "
                "without risking application rejection, please clarify these key details."
            )
        }

