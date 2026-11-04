import re
from typing import Optional, Dict, Any, Tuple
from rag.discovery import LoanDiscoveryProfile, ProvenanceSource, FieldState

def parse_indian_number(text: str) -> Optional[float]:
    """Parses numbers with Indian units (Cr, Crore, Lakh, Lac, L, K, Thousand). Returns Rupees."""
    t = text.lower()
    t = re.sub(r"(?:\brs\.?|\binr\b|₹)", " ", t)
    t = t.replace(",", "").strip()
    
    # Check for range: e.g. "25 - 40 lakhs", "50 to 75 lakh", "1 to 1.5 cr"
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*(cr|crore|lakh|lac|l|k|thousand)?\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)\s*(cr|crore|lakh|lac|l|k|thousand)?", t)
    if range_match:
        low = float(range_match.group(1))
        unit1 = range_match.group(2)
        high = float(range_match.group(3))
        unit2 = range_match.group(4) or unit1
        
        mult = 100000.0 # Default lakh
        if unit2 in ["cr", "crore"]:
            mult = 10000000.0
        elif unit2 in ["lakh", "lac", "l"]:
            mult = 100000.0
        elif unit2 in ["k", "thousand"]:
            mult = 1000.0
        elif high <= 100:
            mult = 100000.0
        elif high > 10000:
            mult = 1.0

        low_val = low * mult if not unit1 or unit1 == unit2 else (low * (10000000.0 if unit1 in ["cr", "crore"] else 100000.0))
        high_val = high * mult
        return (low_val + high_val) / 2.0

    m = re.search(r"(\d+(?:\.\d+)?)\s*(cr|crore|lakh|lac|l|k|thousand)?", t)
    if not m:
        return None
    
    val = float(m.group(1))
    unit = m.group(2)
    
    if unit in ["cr", "crore"]:
        return val * 10000000.0
    elif unit in ["lakh", "lac", "l"]:
        return val * 100000.0
    elif unit in ["k", "thousand"]:
        return val * 1000.0
    elif val > 10000:
        return val
    elif val <= 100: # e.g. "for 50" when in context of lakhs
        return val * 100000.0
    return val

def normalize_match_token(t: str) -> str:
    """Normalizes string for robust option matching (removes symbols, extra spaces, currency)."""
    return re.sub(r"[^\w\d+]+", "", t.lower().replace("₹", "").replace("rs.", "").replace("rupees", ""))

def match_question_bank_options(query: str) -> Dict[str, Any]:
    """Matches text against predefined options in QUESTION_BANK for instant, precise parameter resolution."""
    try:
        from rag.clarification import QUESTION_BANK
    except Exception:
        return {}

    q_norm = normalize_match_token(query)
    extracted: Dict[str, Any] = {}

    for qk, q_item in QUESTION_BANK.items():
        field = q_item["field"]
        for opt in q_item.get("options", []):
            opt_norm = normalize_match_token(opt["label"])
            if not opt_norm:
                continue

            matched = False
            # Check if option label is contained in query, or query equals option label
            if opt_norm in q_norm:
                matched = True
            elif len(q_norm) >= 4 and len(opt_norm) >= 4 and q_norm in opt_norm:
                if len(q_norm) >= len(opt_norm) * 0.65:
                    matched = True

            if matched:
                val = opt["value"]
                if field == "priorities":
                    extracted.setdefault("priorities", [])
                    if val not in extracted["priorities"]:
                        extracted["priorities"].append(val)
                elif field == "self_reported_credit_score":
                    if val == -1:
                        extracted["self_reported_credit_score"] = None
                        extracted["credit_score_range"] = "UNKNOWN"
                    else:
                        extracted["self_reported_credit_score"] = val
                else:
                    extracted[field] = val

    return extracted

def extract_parameters_from_text(query: str) -> Dict[str, Any]:
    """Extracts explicit financial parameters, corrections, and borrower priorities from natural text."""
    # First check direct matches from question bank options
    extracted = match_question_bank_options(query)

    q = query.lower()
    q = re.sub(r"(?:\brs\.?|\binr\b|₹)", " ", q)
    q = q.replace(",", "").strip()
    q = re.sub(r"\bin-hand\b", "in hand", q)
    q = re.sub(r"\btake-home\b", "take home", q)

    # 1. Category Detection
    if any(w in q for w in ["home loan", "homeloan", "housing", "mortgage", "house loan", "plot loan"]):
        extracted["loan_category"] = "Home Loan"
    elif any(w in q for w in ["personal loan", "personalloan", "unsecured loan", "instant loan"]):
        extracted["loan_category"] = "Personal Loan"
    elif any(w in q for w in ["education loan", "study loan", "student loan", "scholar loan", "university"]):
        extracted["loan_category"] = "Education Loan"
    elif any(w in q for w in ["car loan", "auto loan", "vehicle loan", "two wheeler", "bike loan"]):
        extracted["loan_category"] = "Vehicle Loan"
    elif any(w in q for w in ["business loan", "commercial loan", "msme loan", "working capital"]):
        extracted["loan_category"] = "Business Loan"

    # 2. Existing EMI / Obligations (Check first before generic income)
    emi_match = re.search(
        r"(?:existing|other|current|paying|active)\s*(?:monthly\s*)?(?:emi|loans?|debt|repayment|obligation)?\s*(?:of|is|:|-)?\s*(\d+(?:\.\d+)?\s*(?:k|thousand|lakh|lac|l)?)",
        q
    )
    if not emi_match:
        emi_match = re.search(
            r"(\d+(?:\.\d+)?\s*(?:k|thousand|lakh|lac|l)?)\s*(?:(?:pm|per\s*month)?\s*(?:existing|active|current)\s*emi)",
            q
        )
    if emi_match:
        val = parse_indian_number(emi_match.group(1))
        if val is not None:
            extracted["existing_monthly_emi"] = val
    elif any(w in q for w in ["zero emi", "no emi", "no existing emi", "no active loan", "no debt", "debt free"]):
        extracted["existing_monthly_emi"] = 0.0

    # 3. Monthly Income
    # Matches:
    # A. Annual package/ctc: e.g. "ctc 18 lpa", "package 12 lakhs", "annual salary 24 lakh"
    annual_match = re.search(r"(?:annual|annum|ctc|lpa|package)\s*(?:salary|income)?\s*(?:of|is|:)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|l|cr|lpa)?", q)
    if not annual_match:
        annual_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lpa|per\s*annum|pa)\b", q)
    if annual_match:
        ann_val = parse_indian_number(annual_match.group(1))
        if ann_val is not None:
            extracted["monthly_net_income"] = round(ann_val / 12.0)

    if "monthly_net_income" not in extracted:
        # B. Suffix frequency: "80000 per month", "80k/month", "80k pm", "80k a month"
        suffix_match = re.search(
            r"(\d+(?:\.\d+)?\s*(?:cr|crore|lakh|lac|l|k|thousand)?)\s*(?:per\s*month|/\s*month|/\s*mo|\bpm\b|a\s*month|per\s*mo)\b",
            q
        )
        if suffix_match:
            val = parse_indian_number(suffix_match.group(1))
            if val is not None and val >= 1000:
                extracted["monthly_net_income"] = val

    if "monthly_net_income" not in extracted:
        # C. Prefix keywords (handles compound: "monthly in hand", "net take home", "salary", "in hand is 80k")
        income_match = re.search(
            r"(?:net\s*)?(?:monthly\s*)?(?:salary|income|in\s*hand|take\s*home|earnings?|earns?|pay)\s*(?:of|is|:|-|around|approx)?\s*(\d+(?:\.\d+)?\s*(?:cr|crore|lakh|lac|l|k|thousand)?)",
            q
        )
        if not income_match:
            # D. "I earn / earning / drawing"
            income_match = re.search(
                r"(?:i\s+)?(?:earn(?:ing|s)?|drawing|draw)\s*(?:around|approx|about)?\s*(\d+(?:\.\d+)?\s*(?:cr|crore|lakh|lac|l|k|thousand)?)",
                q
            )
        if income_match:
            val = parse_indian_number(income_match.group(1))
            if val is not None:
                extracted["monthly_net_income"] = val

    # 4. Requested Loan Amount
    # Matches: "need 1 crore", "loan of 50 lakh", "looking for 40 lakh", "borrow 60 lakhs", "require 5 lakhs"
    amt_match = re.search(r"(?:need|borrow|loan\s*of|looking\s*for|require|financing\s*of|quantum\s*of|around|want)\s*(?:a\s*)?(?:loan\s*(?:of)?)?\s*(\d+(?:\.\d+)?\s*(?:cr|crore|lakh|lac|l|k|thousand)?)", q)
    if amt_match:
        val = parse_indian_number(amt_match.group(1))
        # Ensure it's not actually the income or emi match
        if val is not None and val >= 50000:
            extracted["requested_amount"] = val
    else:
        # Fallback: standalone "50 lakh loan" or "1 crore home loan"
        standalone = re.search(r"(\d+(?:\.\d+)?\s*(?:cr|crore|lakh|lac|l))\s*(?:home|personal|education|car|auto|business)?\s*loan", q)
        if standalone:
            val = parse_indian_number(standalone.group(1))
            if val is not None:
                extracted["requested_amount"] = val

    # 5. Preferred Tenure
    tenure_match = re.search(r"(\d+)\s*(?:years?|yrs?|yr)\s*(?:tenure|repayment|horizon|duration)?", q)
    if not tenure_match:
        tenure_match = re.search(r"(?:for|over)\s*(\d+)\s*(?:years?|yrs?|yr)\b", q)
    if tenure_match:
        years = int(tenure_match.group(1))
        if 1 <= years <= 35:
            extracted["preferred_tenure_months"] = years * 12
    else:
        month_match = re.search(r"(\d+)\s*(?:months?|mo)\s*(?:tenure)?", q)
        if month_match:
            months = int(month_match.group(1))
            if 6 <= months <= 420:
                extracted["preferred_tenure_months"] = months

    # 6. Maximum / Comfortable Monthly EMI
    max_emi_match = re.search(r"(?:maximum|max|comfortable|afford(?:able)?)\s*(?:emi|monthly\s*payment)?\s*(?:of|is|:)?\s*(\d+(?:\.\d+)?\s*(?:k|thousand|lakh|lac|l)?)", q)
    if max_emi_match:
        val = parse_indian_number(max_emi_match.group(1))
        if val is not None:
            extracted["maximum_monthly_emi"] = val
            extracted["comfortable_monthly_emi"] = val

    # 7. Credit Score / CIBIL
    cibil_match = re.search(r"(?:cibil|credit\s*score)\s*(?:of|is|:)?\s*(\d{3})", q)
    if cibil_match:
        extracted["self_reported_credit_score"] = int(cibil_match.group(1))
    elif any(w in q for w in ["don't know cibil", "dont know cibil", "no cibil", "not aware of cibil", "dont know my score", "unknown cibil"]):
        extracted["self_reported_credit_score"] = None
        extracted["credit_score_range"] = "UNKNOWN"

    # 8. Employment Type & Employer
    if any(w in q for w in ["salaried", "working at", "job", "corporate", "employee", "salary slip"]):
        extracted["employment_type"] = "Salaried"
    elif any(w in q for w in ["self employed", "business owner", "proprietor", "freelancer", "firm", "shop"]):
        extracted["employment_type"] = "Self-Employed"
    elif any(w in q for w in ["doctor", "ca", "lawyer", "professional"]):
        extracted["employment_type"] = "Self-Employed Professional"

    # 9. Priorities & Preferences
    priorities = []
    if any(w in q for w in ["lowest total interest", "lowest interest cost", "save interest", "cheapest overall"]):
        priorities.append("LOWEST_TOTAL_INTEREST")
    if any(w in q for w in ["lower emi", "lowest emi", "minimum emi", "small emi"]):
        priorities.append("LOWER_MONTHLY_EMI")
    if any(w in q for w in ["fast processing", "urgent", "quick sanction", "immediate", "speed"]):
        priorities.append("FAST_PROCESSING")
    if any(w in q for w in ["low fees", "zero fee", "no processing fee", "minimal charges"]):
        priorities.append("LOW_FEES")
    if priorities:
        extracted["priorities"] = priorities

    # 10. Lender Type Preference
    if any(w in q for w in ["public sector", "government bank", "sbi only", "psu bank", "nationalised"]):
        extracted["preferred_lender_type"] = "Public"
    elif any(w in q for w in ["private bank", "private sector", "hdfc or icici"]):
        extracted["preferred_lender_type"] = "Private"

    # 11. Property Value / Purchase Price
    prop_val_match = re.search(r"(?:property\s*(?:value|price|worth)?|purchase\s*price|cost\s*of\s*(?:flat|house|property|apartment)|budget)\s*(?:of|is|:)?\s*(\d+(?:\.\d+)?\s*(?:cr|crore|lakh|lac|l|k)?)", q)
    if prop_val_match:
        val = parse_indian_number(prop_val_match.group(1))
        if val and val >= 100000:
            extracted["property_value"] = val

    # 12. Property Type
    if any(w in q for w in ["ready residential", "ready to move", "ready flat", "ready house", "resale"]):
        extracted["property_type"] = "Ready Residential"
    elif any(w in q for w in ["under construction", "new launch", "pre launch", "builder floor"]):
        extracted["property_type"] = "Under Construction"
    elif any(w in q for w in ["plot", "land", "site purchase"]):
        extracted["property_type"] = "Plot"
    elif any(w in q for w in ["commercial", "office space", "shop"]):
        extracted["property_type"] = "Commercial"

    # 13. City / Location
    city_patterns = [
        ("mumbai", "Mumbai"), ("bombay", "Mumbai"), ("delhi", "Delhi-NCR"), ("ncr", "Delhi-NCR"),
        ("gurgaon", "Delhi-NCR"), ("noida", "Delhi-NCR"), ("bengaluru", "Bengaluru"), ("bangalore", "Bengaluru"),
        ("pune", "Pune"), ("hyderabad", "Hyderabad"), ("chennai", "Chennai"), ("kolkata", "Kolkata"),
        ("ahmedabad", "Ahmedabad"), ("jaipur", "Jaipur"), ("chandigarh", "Chandigarh"), ("lucknow", "Lucknow")
    ]
    for c_kw, c_val in city_patterns:
        if re.search(r"\b" + c_kw + r"\b", q):
            extracted["city"] = c_val
            break

    # 14. Explicit Corrections Detection
    # e.g. "actually my income is 1.5 lakh not 1.2 lakh"
    is_correction = any(w in q for w in ["actually", "correction", "mistake", "not ... but", "not 1."])
    extracted["is_correction"] = is_correction

    # 15. Vehicle Type (Car Loans)
    if any(w in q for w in ["brand new car", "new car", "new vehicle", "showroom"]):
        extracted["vehicle_type"] = "New Car"
    elif any(w in q for w in ["used car", "second hand", "pre owned", "pre-owned"]):
        extracted["vehicle_type"] = "Used Car"

    # 16. Study Destination (Education Loans)
    if any(w in q for w in ["overseas", "abroad", "foreign", "in us", "in usa", "in uk", "in canada", "in germany", "in europe", "in australia", "ms in"]):
        extracted["study_destination"] = "Overseas"
    elif any(w in q for w in ["domestic", "in india", "indian university", "iim", "iit"]):
        extracted["study_destination"] = "Domestic"

    # 17. Education Collateral
    if any(w in q for w in ["collateral free", "without collateral", "unsecured", "no collateral", "cgfsel"]):
        extracted["collateral_type"] = "Unsecured"
    elif any(w in q for w in ["with collateral", "property collateral", "secured", "pledge", "fixed deposit"]):
        extracted["collateral_type"] = "Collateralized"

    # 18. Salary Bank
    if any(w in q for w in ["salary in sbi", "sbi salary", "salary account sbi", "account in sbi"]):
        extracted["salary_bank"] = "SBI"
    elif any(w in q for w in ["salary in hdfc", "hdfc salary", "salary account hdfc", "account in hdfc"]):
        extracted["salary_bank"] = "HDFC"
    elif any(w in q for w in ["salary in icici", "icici salary", "salary account icici"]):
        extracted["salary_bank"] = "ICICI"

    return extracted

def update_profile_from_query(
    query: str,
    current_profile: Optional[LoanDiscoveryProfile] = None,
    user_profile_dict: Optional[Dict[str, Any]] = None
) -> LoanDiscoveryProfile:
    """Incrementally updates the LoanDiscoveryProfile across turns without resetting previous facts."""
    if current_profile is None:
        current_profile = LoanDiscoveryProfile()

    # Pre-fill from UI Profile Drawer if present and not yet user-provided
    if user_profile_dict:
        if user_profile_dict.get("Employment") and not current_profile.employment_type.is_known():
            current_profile.employment_type.set_user_value(user_profile_dict["Employment"])
        if user_profile_dict.get("CIBIL Score") and not current_profile.self_reported_credit_score.is_known():
            current_profile.self_reported_credit_score.set_user_value(int(user_profile_dict["CIBIL Score"]))
        if user_profile_dict.get("Category Filter") and user_profile_dict["Category Filter"] != "All":
            current_profile.loan_category.set_user_value(user_profile_dict["Category Filter"])
        if user_profile_dict.get("Income") and not current_profile.monthly_net_income.is_known():
            num = parse_indian_number(str(user_profile_dict["Income"]))
            if num:
                current_profile.monthly_net_income.set_user_value(num)
        if user_profile_dict.get("Requested Amount") and not current_profile.requested_amount.is_known():
            num = parse_indian_number(str(user_profile_dict["Requested Amount"]))
            if num:
                current_profile.requested_amount.set_user_value(num)

    extracted = extract_parameters_from_text(query)
    modified = False

    if "loan_category" in extracted:
        current_profile.loan_category.set_user_value(extracted["loan_category"])
        modified = True

    if "requested_amount" in extracted:
        current_profile.requested_amount.set_user_value(extracted["requested_amount"])
        modified = True

    if "monthly_net_income" in extracted:
        current_profile.monthly_net_income.set_user_value(extracted["monthly_net_income"])
        modified = True

    if "existing_monthly_emi" in extracted:
        current_profile.existing_monthly_emi.set_user_value(extracted["existing_monthly_emi"])
        modified = True

    if "preferred_tenure_months" in extracted:
        current_profile.preferred_tenure_months.set_user_value(extracted["preferred_tenure_months"])
        modified = True

    if "maximum_monthly_emi" in extracted:
        current_profile.maximum_monthly_emi.set_user_value(extracted["maximum_monthly_emi"])
        modified = True

    if "self_reported_credit_score" in extracted:
        if extracted["self_reported_credit_score"] is not None:
            current_profile.self_reported_credit_score.set_user_value(extracted["self_reported_credit_score"])
        else:
            current_profile.self_reported_credit_score.state = FieldState.DECLINED
            current_profile.credit_score_range.set_user_value("UNKNOWN")
        modified = True

    if "employment_type" in extracted:
        current_profile.employment_type.set_user_value(extracted["employment_type"])
        modified = True

    if "preferred_lender_type" in extracted:
        current_profile.preferred_lender_type.set_user_value(extracted["preferred_lender_type"])
        modified = True

    if "property_value" in extracted:
        current_profile.property_value.set_user_value(extracted["property_value"])
        modified = True

    if "property_type" in extracted:
        current_profile.property_type.set_user_value(extracted["property_type"])
        modified = True

    if "city" in extracted:
        current_profile.city.set_user_value(extracted["city"])
        modified = True

    if "vehicle_type" in extracted:
        current_profile.vehicle_type.set_user_value(extracted["vehicle_type"])
        modified = True

    if "study_destination" in extracted:
        current_profile.study_destination.set_user_value(extracted["study_destination"])
        modified = True

    if "collateral_type" in extracted:
        current_profile.collateral_type.set_user_value(extracted["collateral_type"])
        modified = True

    if "salary_bank" in extracted:
        current_profile.salary_bank.set_user_value(extracted["salary_bank"])
        modified = True

    if "priorities" in extracted:
        for p in extracted["priorities"]:
            if p not in current_profile.priorities:
                current_profile.priorities.append(p)
        modified = True

    if modified:
        current_profile.version += 1

    return current_profile

