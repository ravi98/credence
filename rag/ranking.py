import math
from typing import List, Dict, Any
from rag.discovery import LoanDiscoveryProfile

def calculate_monthly_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    if tenure_months <= 0 or principal <= 0:
        return 0.0
    r = (annual_rate / 100.0) / 12.0
    if r == 0:
        return principal / tenure_months
    emi = (principal * r * math.pow(1 + r, tenure_months)) / (math.pow(1 + r, tenure_months) - 1)
    return emi

class DeterministicRanker:
    """
    Ranks qualified loan candidates using deterministic mathematical criteria
    and customer stated priorities (lowest interest vs lowest EMI vs lowest fees).
    """

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        profile: LoanDiscoveryProfile
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        principal = profile.requested_amount.value or 5000000.0
        tenure_months = profile.preferred_tenure_months.value or 240
        cibil = profile.self_reported_credit_score.value or 750
        priorities = profile.priorities or []
        max_comfortable_emi = profile.maximum_monthly_emi.value

        scored = []
        for cand in candidates:
            m = cand["metadata"]
            base_rate = float(m.get("min_rate_num") or 8.5)

            # Risk-tier spread adjustment based on CIBIL
            effective_rate = base_rate
            if cibil < 700:
                effective_rate += 0.65
            elif cibil < 750:
                effective_rate += 0.25

            # Calculate exact candidate EMI
            try:
                max_ty = float(m.get("max_tenure_years") or 30)
            except Exception:
                max_ty = 30.0
            cand_tenure = min(int(tenure_months), int(max_ty * 12))
            est_emi = calculate_monthly_emi(principal, effective_rate, cand_tenure)
            total_interest = (est_emi * cand_tenure) - principal

            # Base score (lower total cost is better)
            score = effective_rate * 10.0

            # Priority modifiers
            if "LOWEST_TOTAL_INTEREST" in priorities:
                score += (total_interest / 100000.0) * 0.5
            elif "LOWER_MONTHLY_EMI" in priorities:
                score += (est_emi / 10000.0) * 0.8
            elif "FAST_PROCESSING" in priorities:
                sector = str(m.get("sector") or "").lower()
                if "private" in sector:
                    score -= 2.0

            # Decision Impact: Salary relationship bank preference
            if profile.salary_bank.is_known():
                sal_bank = profile.salary_bank.value.lower()
                inst = str(m.get("institution") or "").lower()
                if sal_bank in inst:
                    score -= 3.0

            # Decision Impact: Dedicated Plot/Land match
            is_plot_match = False
            if profile.property_type.value == "Plot":
                s_name = str(m.get("scheme_name") or "").lower()
                if any(w in s_name for w in ["plot", "land", "realty"]):
                    score -= 4.0
                    is_plot_match = True

            # Processing fee bonus
            p_fee = str(m.get("processing_fee") or "").lower()
            if "nil" in p_fee or "zero" in p_fee or "waived" in p_fee:
                score -= 1.5

            # Check if exceeds comfortable EMI ceiling
            emi_fits_ceiling = True
            if max_comfortable_emi and est_emi > max_comfortable_emi:
                emi_fits_ceiling = False
                score += 5.0 # Penalty for exceeding customer's hard budget

            # Assign explanatory badge
            badge = "Balanced Value"
            if is_plot_match:
                badge = "Dedicated Plot Financing"
            elif profile.salary_bank.is_known() and profile.salary_bank.value.lower() in str(m.get("institution") or "").lower():
                badge = "Salary Bank Pre-Approval"
            elif "FAST_PROCESSING" in priorities and "private" in str(m.get("sector") or "").lower():
                badge = "Fast Digital Sanction"
            elif base_rate <= 7.5:
                badge = "Lowest Base Rate"
            elif "nil" in p_fee or "zero" in p_fee:
                badge = "Zero Processing Fee"
            elif (m.get("max_tenure_years") or 0) >= 30:
                badge = "Extended 30Y Tenure"

            cand_copy = dict(cand)
            cand_copy["ranking_details"] = {
                "effective_rate": round(effective_rate, 2),
                "tenure_months": cand_tenure,
                "tenure_years": cand_tenure // 12,
                "estimated_monthly_emi": round(est_emi),
                "total_interest_payable": round(total_interest),
                "badge": badge,
                "fits_emi_budget": emi_fits_ceiling,
                "rank_score": score
            }
            scored.append(cand_copy)

        # Sort by deterministic rank score (lower score = higher rank)
        scored.sort(key=lambda x: x["ranking_details"]["rank_score"])
        return scored

