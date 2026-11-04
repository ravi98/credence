import os
import json
from typing import List, Dict, Any, Optional
from rag.discovery import LoanDiscoveryProfile

MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "catalog_manifest.json")
try:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        ALL_SCHEMES = json.load(f).get("schemes", [])
except Exception:
    ALL_SCHEMES = []

class StructuredCandidateRetriever:
    """
    Discovers candidate loan products from the authoritative structured catalog
    with lender deduplication, hard constraint filtering, and sector diversity.
    """

    def __init__(self, schemes: Optional[List[Dict[str, Any]]] = None):
        self.schemes = schemes if schemes is not None else ALL_SCHEMES

    def filter_and_deduplicate(
        self,
        profile: LoanDiscoveryProfile,
        max_results: int = 4
    ) -> List[Dict[str, Any]]:
        category = profile.loan_category.value or "Home Loan"
        requested_amt = profile.requested_amount.value or 0
        income = profile.monthly_net_income.value or 0
        lender_type_pref = profile.preferred_lender_type.value # "Public", "Private", or None

        candidates = []

        # 1. Hard Filter on Category
        for s in self.schemes:
            if s.get("category", "").lower() != category.lower():
                continue

            # Amount bounds check
            max_amt_lakhs = s.get("max_amount_lakhs")
            min_amt_lakhs = s.get("min_amount_lakhs")
            req_lakhs = requested_amt / 100000.0 if requested_amt > 0 else 0

            if req_lakhs > 0 and max_amt_lakhs and req_lakhs > max_amt_lakhs:
                continue
            if req_lakhs > 0 and min_amt_lakhs and req_lakhs < min_amt_lakhs:
                continue

            # Lender type preference check
            if lender_type_pref and lender_type_pref in ["Public", "Private"]:
                s_sector = s.get("sector", "")
                if lender_type_pref.lower() not in s_sector.lower():
                    continue

            candidates.append(s)

        # 2. Lender-Level Deduplication & Diversity
        # We ensure a single bank does not occupy all slots. Group by institution.
        by_institution: Dict[str, List[Dict[str, Any]]] = {}
        for c in candidates:
            inst = c.get("institution", "Other")
            if inst not in by_institution:
                by_institution[inst] = []
            by_institution[inst].append(c)

        # If user did not restrict to single sector, balance Public and Private lenders
        public_candidates = []
        private_candidates = []

        for inst, inst_schemes in by_institution.items():
            # Apply Decision Impact on collateral / product type
            best_scheme = None

            # 1. Plot/Land Purchase preference
            if profile.property_type.value == "Plot":
                plot_schemes = [s for s in inst_schemes if any(w in s.get("scheme_name", "").lower() for w in ["plot", "land", "realty"])]
                if plot_schemes:
                    best_scheme = sorted(plot_schemes, key=lambda x: x.get("min_rate_num") or 99.0)[0]

            # 2. Overseas education preference
            elif profile.study_destination.value == "Overseas":
                overseas_schemes = [s for s in inst_schemes if any(w in s.get("scheme_name", "").lower() for w in ["overseas", "global", "foreign", "international"])]
                if overseas_schemes:
                    best_scheme = sorted(overseas_schemes, key=lambda x: x.get("min_rate_num") or 99.0)[0]

            # 3. Used/Pre-owned vehicle preference
            elif profile.vehicle_type.value == "Used Car":
                used_schemes = [s for s in inst_schemes if any(w in s.get("scheme_name", "").lower() for w in ["used", "pre-owned", "certified pre-owned"])]
                if used_schemes:
                    best_scheme = sorted(used_schemes, key=lambda x: x.get("min_rate_num") or 99.0)[0]

            # Default: Pick best rate scheme per institution
            if not best_scheme:
                best_scheme = sorted(inst_schemes, key=lambda x: x.get("min_rate_num") or 99.0)[0]

            sector = best_scheme.get("sector", "").lower()
            if "public" in sector:
                public_candidates.append(best_scheme)
            else:
                private_candidates.append(best_scheme)

        # Sort each pool by interest rate
        public_candidates.sort(key=lambda x: x.get("min_rate_num") or 99.0)
        private_candidates.sort(key=lambda x: x.get("min_rate_num") or 99.0)

        selected = []
        # Interleave public and private to guarantee healthy coverage
        p_idx, pr_idx = 0, 0
        while len(selected) < max_results and (p_idx < len(public_candidates) or pr_idx < len(private_candidates)):
            if p_idx < len(public_candidates):
                selected.append(public_candidates[p_idx])
                p_idx += 1
            if len(selected) < max_results and pr_idx < len(private_candidates):
                selected.append(private_candidates[pr_idx])
                pr_idx += 1

        # Fallback if pools were lopsided
        if not selected and candidates:
            # Sort all unique institutions
            unique_inst_schemes = [v[0] for v in by_institution.values()]
            unique_inst_schemes.sort(key=lambda x: x.get("min_rate_num") or 99.0)
            selected = unique_inst_schemes[:max_results]

        # Format candidates as graph-compatible objects
        formatted = []
        for s in selected:
            formatted.append({
                "metadata": s,
                "document": s.get("compact_summary", f"{s.get('scheme_name')} by {s.get('institution')}")
            })

        return formatted

