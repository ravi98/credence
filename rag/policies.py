"""Declarative Loan Category Policies for Indian Retail Banking.
Centralizes verified eligibility baselines, income floors, age windows, and regulatory FOIR ceilings.
"""

CATEGORY_POLICIES = {
    "Home Loan": {
        "min_individual_income": 12000,          # Lowest affordable scheme in catalog (Kotak Vishwas)
        "standard_min_income": 20000,            # Public Sector Banks entry floor
        "metro_min_income": 25000,               # Private Commercial Banks Tier-1 floor
        "max_foir": 0.50,                        # Max 50% EMI to net monthly income
        "min_age": 18,
        "max_age": 70,
        "min_cibil": 700,
        "guidance": (
            "- Standard Commercial Banks (SBI, Federal Bank, Kotak, HDFC) require net monthly salary of Rs. 15,000–25,000.\n"
            "- Affordable housing schemes (Kotak Vishwas) require at least Rs. 12,000/month.\n"
            "- Regulatory FOIR (40-50%) caps allowable monthly EMI.\n"
            "- Solutions for lower income: Add an earning co-applicant, explore PMAY/affordable housing HFCs, or save a higher down payment."
        )
    },
    "Personal Loan": {
        "min_individual_income": 15000,          # Unsecured personal loan absolute minimum
        "standard_min_income": 25000,            # Major private banks baseline
        "metro_min_income": 30000,
        "max_foir": 0.40,                        # Tighter debt ceiling for unsecured loans
        "min_age": 21,
        "max_age": 60,
        "min_cibil": 700,
        "guidance": (
            "- Major Indian banks require minimum net salary of Rs. 15,000 to Rs. 25,000/month for unsecured personal loans.\n"
            "- Salaried applicants need at least 1-2 years continuous employment stability.\n"
            "- Alternative for lower income: Consider secured loans (gold loan, loan against FD) or applying with a co-borrower."
        )
    },
    "Vehicle Loan": {
        "min_individual_income": 15000,          # 4-wheeler entry floor
        "two_wheeler_min_income": 10000,         # 2-wheeler entry floor
        "standard_min_income": 20000,
        "max_foir": 0.50,
        "min_age": 21,
        "max_age": 65,
        "min_cibil": 650,
        "guidance": (
            "- 4-Wheeler Car Loans require minimum net monthly income of Rs. 15,000–20,000.\n"
            "- 2-Wheeler Loans start at Rs. 10,000/month.\n"
            "- LTV typically covers 85%–100% on-road price depending on CIBIL score."
        )
    },
    "Education Loan": {
        "min_individual_income": 0,              # Student has no income requirement
        "cgfsel_collateral_free_cap": 7.5,        # Rs. 7.5 Lakhs collateral-free under CGFSEL
        "standard_min_income": 0,
        "max_foir": 0.50,                        # Assessed on co-borrower (parent/guardian)
        "min_age": 16,
        "max_age": 35,
        "min_cibil": 650,
        "guidance": (
            "- Confirmed admission to recognized domestic or overseas university is mandatory.\n"
            "- Loans up to Rs. 7.5 Lakhs are collateral-free with zero margin money under CGFSEL guarantee.\n"
            "- Up to 8 years full interest tax deduction under Section 80E with zero upper limit."
        )
    }
}
