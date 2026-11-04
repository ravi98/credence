from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from rag.discovery import LoanDiscoveryProfile, LoanCategory, FieldState

class ReadinessLevel(str, Enum):
    PRELIMINARY = "PRELIMINARY"
    PERSONALIZED = "PERSONALIZED"
    ELIGIBILITY_ASSESSED = "ELIGIBILITY_ASSESSED"

class DecisionImpactType(str, Enum):
    ELIGIBILITY_FILTER = "ELIGIBILITY_FILTER"
    AFFORDABILITY_ASSESSMENT = "AFFORDABILITY_ASSESSMENT"
    PREFERENCE_RANKING = "PREFERENCE_RANKING"
    PRODUCT_CUSTOMIZATION = "PRODUCT_CUSTOMIZATION"

class QuestionPriority(str, Enum):
    CRITICAL_ELIGIBILITY = "CRITICAL_ELIGIBILITY"
    AFFORDABILITY_BLOCKER = "AFFORDABILITY_BLOCKER"
    PREFERENCE_TUNING = "PREFERENCE_TUNING"
    DOCUMENTATION_POLICING = "DOCUMENTATION_POLICING"

class DecisionImpact(BaseModel):
    impact_type: DecisionImpactType
    affected_attribute: str
    operation: str
    rule_description: str

# Comprehensive Question-to-Decision Knowledge Registry
QUESTION_BANK: Dict[str, Dict[str, Any]] = {
    # ==================== HOME LOAN QUESTIONS ====================
    "HOME_LOAN_AMOUNT": {
        "id": "HOME_LOAN_AMOUNT",
        "field": "requested_amount",
        "loan_categories": ["Home Loan"],
        "priority": QuestionPriority.CRITICAL_ELIGIBILITY.value,
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
        "allow_custom_input": True,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.ELIGIBILITY_FILTER.value,
                "affected_attribute": "rbi_ltv_ceiling",
                "operation": "DETERMINE_LTV_TIER",
                "rule_description": "Enforces statutory RBI LTV caps (90% <=30L, 80% 30-75L, 75% >75L)."
            },
            {
                "impact_type": DecisionImpactType.AFFORDABILITY_ASSESSMENT.value,
                "affected_attribute": "monthly_installment",
                "operation": "CALCULATE_BASE_EMI",
                "rule_description": "Sets the principal amount required for exact EMI and FOIR calculations."
            }
        ]
    },
    "HOME_LOAN_TENURE": {
        "id": "HOME_LOAN_TENURE",
        "field": "preferred_tenure_months",
        "loan_categories": ["Home Loan"],
        "priority": QuestionPriority.AFFORDABILITY_BLOCKER.value,
        "question": "What repayment tenure are you considering?",
        "explanation": "Tenure determines your monthly EMI and total interest outflow. Longer tenures lower your monthly installment but increase cumulative interest.",
        "input_type": "select",
        "options": [
            {"label": "15 Years (180 mo)", "value": 180},
            {"label": "20 Years (240 mo)", "value": 240},
            {"label": "25 Years (300 mo)", "value": 300},
            {"label": "30 Years (360 mo)", "value": 360}
        ],
        "allow_custom_input": False,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.AFFORDABILITY_ASSESSMENT.value,
                "affected_attribute": "debt_service_ratio",
                "operation": "COMPUTE_AMORTIZATION",
                "rule_description": "Determines monthly repayment obligation against borrower net monthly income."
            },
            {
                "impact_type": DecisionImpactType.PREFERENCE_RANKING.value,
                "affected_attribute": "total_interest_outflow",
                "operation": "OPTIMIZE_TENURE_COST",
                "rule_description": "Influences candidate ranking based on overall interest expense minimization."
            }
        ]
    },
    "PROPERTY_VALUE": {
        "id": "PROPERTY_VALUE",
        "field": "property_value",
        "loan_categories": ["Home Loan"],
        "priority": QuestionPriority.CRITICAL_ELIGIBILITY.value,
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
        "allow_custom_input": True,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.ELIGIBILITY_FILTER.value,
                "affected_attribute": "max_sanction_amount",
                "operation": "EVALUATE_MAX_PERMISSIBLE_LOAN",
                "rule_description": "Calculates maximum allowable borrowing quantum based on property valuation."
            }
        ]
    },
    "PROPERTY_TYPE": {
        "id": "PROPERTY_TYPE",
        "field": "property_type",
        "loan_categories": ["Home Loan"],
        "priority": QuestionPriority.CRITICAL_ELIGIBILITY.value,
        "question": "What is the property type or status?",
        "explanation": "Standard 90% LTV applies to residential apartments/villas. Commercial units and land/plots are capped at 60%–70% LTV.",
        "input_type": "select",
        "options": [
            {"label": "Ready-to-move Residential", "value": "Ready Residential"},
            {"label": "Under Construction (Pre-EMI)", "value": "Under Construction"},
            {"label": "Plot / Land Purchase", "value": "Plot"},
            {"label": "Commercial Property", "value": "Commercial"}
        ],
        "allow_custom_input": False,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.ELIGIBILITY_FILTER.value,
                "affected_attribute": "scheme_collateral_suitability",
                "operation": "FILTER_SCHEMES_BY_COLLATERAL",
                "rule_description": "Filters out standard home loans for plot purchases and prioritizes dedicated plot/land acquisition loans."
            },
            {
                "impact_type": DecisionImpactType.PRODUCT_CUSTOMIZATION.value,
                "affected_attribute": "disbursement_structure",
                "operation": "ACCOUNT_FOR_PRE_EMI",
                "rule_description": "Under construction properties require construction-linked staged disbursement and pre-EMI interest handling."
            }
        ]
    },
    "PROPERTY_LOCATION": {
        "id": "PROPERTY_LOCATION",
        "field": "city",
        "loan_categories": ["Home Loan"],
        "priority": QuestionPriority.PREFERENCE_TUNING.value,
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
        "allow_custom_input": True,
        "allow_skip": True,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.ELIGIBILITY_FILTER.value,
                "affected_attribute": "geographic_sanction_cap",
                "operation": "APPLY_METRO_VALUATION_CRITERIA",
                "rule_description": "Validates lender branch jurisdiction and circle rate compliance."
            }
        ]
    },

    # ==================== COMMON FINANCIAL UNDERWRITING QUESTIONS ====================
    "MONTHLY_NET_INCOME": {
        "id": "MONTHLY_NET_INCOME",
        "field": "monthly_net_income",
        "loan_categories": ["Home Loan", "Personal Loan", "Vehicle Loan", "Education Loan", "Business Loan"],
        "priority": QuestionPriority.AFFORDABILITY_BLOCKER.value,
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
        "allow_custom_input": True,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.AFFORDABILITY_ASSESSMENT.value,
                "affected_attribute": "max_foir_capacity",
                "operation": "COMPUTE_FOIR_CEILING",
                "rule_description": "Sets upper limit on aggregate debt obligations (50% to 60% of net monthly income)."
            },
            {
                "impact_type": DecisionImpactType.ELIGIBILITY_FILTER.value,
                "affected_attribute": "minimum_salary_threshold",
                "operation": "SCREEN_MINIMUM_INCOME",
                "rule_description": "Excludes prime bank schemes where applicant income is below institutional threshold."
            }
        ]
    },
    "EXISTING_MONTHLY_EMI": {
        "id": "EXISTING_MONTHLY_EMI",
        "field": "existing_monthly_emi",
        "loan_categories": ["Home Loan", "Personal Loan", "Vehicle Loan", "Education Loan", "Business Loan"],
        "priority": QuestionPriority.AFFORDABILITY_BLOCKER.value,
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
        "allow_custom_input": True,
        "allow_skip": True,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.AFFORDABILITY_ASSESSMENT.value,
                "affected_attribute": "available_emi_headroom",
                "operation": "DEDUCT_OBLIGATIONS_FROM_FOIR",
                "rule_description": "Calculates available monthly cashflow for servicing the proposed new loan."
            }
        ]
    },
    "EMPLOYMENT_TYPE": {
        "id": "EMPLOYMENT_TYPE",
        "field": "employment_type",
        "loan_categories": ["Home Loan", "Personal Loan", "Vehicle Loan", "Business Loan"],
        "priority": QuestionPriority.PREFERENCE_TUNING.value,
        "question": "What is your employment profile?",
        "explanation": "Salaried corporate employees often qualify for special discounted EBLR interest rate spreads and waived processing fees.",
        "input_type": "select",
        "options": [
            {"label": "Salaried (MNC / Listed / Govt)", "value": "Salaried"},
            {"label": "Self-Employed Business / Proprietor", "value": "Self-Employed"},
            {"label": "Professional (Doctor / CA / Architect)", "value": "Self-Employed Professional"}
        ],
        "allow_custom_input": False,
        "allow_skip": True,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.ELIGIBILITY_FILTER.value,
                "affected_attribute": "scheme_employment_criteria",
                "operation": "VALIDATE_EMPLOYMENT_CATEGORY",
                "rule_description": "Filters schemes restricted exclusively to salaried or professional borrowers."
            },
            {
                "impact_type": DecisionImpactType.PREFERENCE_RANKING.value,
                "affected_attribute": "corporate_concession",
                "operation": "APPLY_PRIME_RATE_CONCESSION",
                "rule_description": "Applies interest concessions (up to 15-25 bps) for prime salaried corporate employees."
            }
        ]
    },
    "CIBIL_SCORE_TIER": {
        "id": "CIBIL_SCORE_TIER",
        "field": "self_reported_credit_score",
        "loan_categories": ["Home Loan", "Personal Loan", "Vehicle Loan", "Education Loan", "Business Loan"],
        "priority": QuestionPriority.PREFERENCE_TUNING.value,
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
        "allow_custom_input": True,
        "allow_skip": True,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.PREFERENCE_RANKING.value,
                "affected_attribute": "eblr_risk_spread",
                "operation": "CALIBRATE_RISK_PRICING",
                "rule_description": "Applies bank spread markups: 0 for 750+, +25 bps for 700-749, +65 bps for <700."
            }
        ]
    },
    "BORROWER_PRIORITY": {
        "id": "BORROWER_PRIORITY",
        "field": "priorities",
        "loan_categories": ["Home Loan", "Personal Loan", "Vehicle Loan", "Education Loan", "Business Loan"],
        "priority": QuestionPriority.PREFERENCE_TUNING.value,
        "question": "What matters most to you in this loan?",
        "explanation": "We use your priority to rank products that minimize overall interest expense versus those that minimize monthly cash outflow.",
        "input_type": "select",
        "options": [
            {"label": "Lowest Total Interest Cost", "value": "LOWEST_TOTAL_INTEREST"},
            {"label": "Lowest Monthly Installment (EMI)", "value": "LOWER_MONTHLY_EMI"},
            {"label": "Minimal Processing Fees & Charges", "value": "LOW_FEES"},
            {"label": "Fastest Sanction & Approval", "value": "FAST_PROCESSING"}
        ],
        "allow_custom_input": False,
        "allow_skip": True,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.PREFERENCE_RANKING.value,
                "affected_attribute": "ranking_objective",
                "operation": "APPLY_OBJECTIVE_WEIGHTS",
                "rule_description": "Sorts candidate schemes deterministically by total outflow, EMI size, or fee minimization."
            }
        ]
    },

    # ==================== PERSONAL LOAN QUESTIONS ====================
    "PERSONAL_LOAN_AMOUNT": {
        "id": "PERSONAL_LOAN_AMOUNT",
        "field": "requested_amount",
        "loan_categories": ["Personal Loan"],
        "priority": QuestionPriority.CRITICAL_ELIGIBILITY.value,
        "question": "How much personal loan funding do you require?",
        "explanation": "Personal loans are unsecured; maximum loan quantum is capped at 10x to 15x of your monthly take-home salary.",
        "input_type": "currency",
        "placeholder": "e.g. 5,00,000",
        "options": [
            {"label": "₹1 – ₹3 Lakhs", "value": 200000},
            {"label": "₹3 – ₹6 Lakhs", "value": 450000},
            {"label": "₹6 – ₹10 Lakhs", "value": 800000},
            {"label": "₹10 Lakhs+", "value": 1200000}
        ],
        "allow_custom_input": True,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.AFFORDABILITY_ASSESSMENT.value,
                "affected_attribute": "income_multiplier_eligibility",
                "operation": "CHECK_PERSONAL_LOAN_SALARY_MULTIPLIER",
                "rule_description": "Validates that requested amount does not exceed maximum salary multiplier."
            }
        ]
    },
    "PERSONAL_LOAN_TENURE": {
        "id": "PERSONAL_LOAN_TENURE",
        "field": "preferred_tenure_months",
        "loan_categories": ["Personal Loan"],
        "priority": QuestionPriority.AFFORDABILITY_BLOCKER.value,
        "question": "What repayment duration fits your budget?",
        "explanation": "Personal loans typically range from 1 to 5 years (12 to 60 months). Shorter terms significantly reduce cumulative interest charges.",
        "input_type": "select",
        "options": [
            {"label": "1 Year (12 mo)", "value": 12},
            {"label": "2 Years (24 mo)", "value": 24},
            {"label": "3 Years (36 mo)", "value": 36},
            {"label": "5 Years (60 mo)", "value": 60}
        ],
        "allow_custom_input": False,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.AFFORDABILITY_ASSESSMENT.value,
                "affected_attribute": "unsecured_emi_burden",
                "operation": "COMPUTE_UNSECURED_EMI",
                "rule_description": "Calculates monthly repayment on higher unsecured interest rate benchmarks (10.5%–14.5%)."
            }
        ]
    },
    "SALARY_CREDIT_BANK": {
        "id": "SALARY_CREDIT_BANK",
        "field": "salary_bank",
        "loan_categories": ["Personal Loan"],
        "priority": QuestionPriority.PREFERENCE_TUNING.value,
        "question": "Which bank holds your primary salary account?",
        "explanation": "Your salary account bank often offers pre-approved instant disbursals, zero paperwork, and lower processing charges.",
        "input_type": "select",
        "options": [
            {"label": "State Bank of India (SBI)", "value": "SBI"},
            {"label": "HDFC Bank", "value": "HDFC"},
            {"label": "ICICI Bank", "value": "ICICI"},
            {"label": "Axis / Kotak / Other", "value": "Private / Other"}
        ],
        "allow_custom_input": False,
        "allow_skip": True,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.PREFERENCE_RANKING.value,
                "affected_attribute": "relationship_bank_preapproval",
                "operation": "BOOST_RELATIONSHIP_LENDER",
                "rule_description": "Prioritizes salary account bank for fastest digital disbursement."
            }
        ]
    },

    # ==================== VEHICLE / CAR LOAN QUESTIONS ====================
    "VEHICLE_TYPE": {
        "id": "VEHICLE_TYPE",
        "field": "vehicle_type",
        "loan_categories": ["Vehicle Loan"],
        "priority": QuestionPriority.CRITICAL_ELIGIBILITY.value,
        "question": "Are you purchasing a new or pre-owned (used) vehicle?",
        "explanation": "New car loans qualify for lowest interest rates (~8.75%–9.25%), whereas used cars attract an interest markup of 2.0% to 3.5% p.a.",
        "input_type": "select",
        "options": [
            {"label": "Brand New Car", "value": "New Car"},
            {"label": "Certified Pre-Owned / Used Car", "value": "Used Car"}
        ],
        "allow_custom_input": False,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.ELIGIBILITY_FILTER.value,
                "affected_attribute": "vehicle_interest_rate_bracket",
                "operation": "FILTER_CAR_LOAN_SCHEMES",
                "rule_description": "Switches between new vehicle and pre-owned vehicle loan scheme schedules."
            }
        ]
    },
    "CAR_LOAN_AMOUNT": {
        "id": "CAR_LOAN_AMOUNT",
        "field": "requested_amount",
        "loan_categories": ["Vehicle Loan"],
        "priority": QuestionPriority.CRITICAL_ELIGIBILITY.value,
        "question": "What is the approximate vehicle loan amount you need?",
        "explanation": "Banks typically fund 85% to 90% of the vehicle's on-road price (ex-showroom + RTO road tax + insurance).",
        "input_type": "currency",
        "placeholder": "e.g. 10,00,000",
        "options": [
            {"label": "₹4 – ₹7 Lakhs", "value": 550000},
            {"label": "₹7 – ₹12 Lakhs", "value": 950000},
            {"label": "₹12 – ₹20 Lakhs", "value": 1500000},
            {"label": "₹20 Lakhs+", "value": 2500000}
        ],
        "allow_custom_input": True,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.AFFORDABILITY_ASSESSMENT.value,
                "affected_attribute": "auto_loan_outflow",
                "operation": "COMPUTE_VEHICLE_EMI",
                "rule_description": "Calculates monthly repayment and debt servicing obligations for auto loans."
            }
        ]
    },
    "CAR_LOAN_TENURE": {
        "id": "CAR_LOAN_TENURE",
        "field": "preferred_tenure_months",
        "loan_categories": ["Vehicle Loan"],
        "priority": QuestionPriority.AFFORDABILITY_BLOCKER.value,
        "question": "What car loan repayment tenure do you prefer?",
        "explanation": "Car loans allow repayment up to 7 years (84 months). 5 years is the industry standard for minimizing asset depreciation vs debt.",
        "input_type": "select",
        "options": [
            {"label": "3 Years (36 mo)", "value": 36},
            {"label": "5 Years (60 mo)", "value": 60},
            {"label": "7 Years (84 mo)", "value": 84}
        ],
        "allow_custom_input": False,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.AFFORDABILITY_ASSESSMENT.value,
                "affected_attribute": "auto_loan_duration",
                "operation": "SET_AUTO_TENURE",
                "rule_description": "Sets auto loan amortization duration up to maximum 84 months."
            }
        ]
    },

    # ==================== EDUCATION LOAN QUESTIONS ====================
    "EDUCATION_DESTINATION": {
        "id": "EDUCATION_DESTINATION",
        "field": "study_destination",
        "loan_categories": ["Education Loan"],
        "priority": QuestionPriority.CRITICAL_ELIGIBILITY.value,
        "question": "Where is the course of study located?",
        "explanation": "Overseas studies require foreign currency tuition remittances, visa financial clearance, and distinct underwriting norms.",
        "input_type": "select",
        "options": [
            {"label": "Domestic (India)", "value": "Domestic"},
            {"label": "Overseas (US / Canada / UK / EU / Australia)", "value": "Overseas"}
        ],
        "allow_custom_input": False,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.ELIGIBILITY_FILTER.value,
                "affected_attribute": "education_scheme_tier",
                "operation": "FILTER_OVERSEAS_DOMESTIC_EDUCATION",
                "rule_description": "Selects specialized overseas study loan schemes with living expense coverage and moratoriums."
            }
        ]
    },
    "EDUCATION_COLLATERAL": {
        "id": "EDUCATION_COLLATERAL",
        "field": "collateral_type",
        "loan_categories": ["Education Loan"],
        "priority": QuestionPriority.CRITICAL_ELIGIBILITY.value,
        "question": "Can you offer tangible property or liquid collateral for the education loan?",
        "explanation": "Government CGFSEL guarantees collateral-free education loans up to ₹7.5 Lakhs. Loans above ₹7.5L to ₹1.5 Cr+ typically require property security or a creditworthy co-borrower.",
        "input_type": "select",
        "options": [
            {"label": "Collateral-Free / Unsecured", "value": "Unsecured"},
            {"label": "Tangible Immovable Property / Fixed Deposit", "value": "Collateralized"}
        ],
        "allow_custom_input": False,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.ELIGIBILITY_FILTER.value,
                "affected_attribute": "collateral_eligibility_cap",
                "operation": "VERIFY_COLLATERAL_LIMITS",
                "rule_description": "Filters collateral-free limits (RBI CGFSEL ₹7.5L cap) versus secured large-quantum schemes."
            }
        ]
    },
    "EDUCATION_LOAN_AMOUNT": {
        "id": "EDUCATION_LOAN_AMOUNT",
        "field": "requested_amount",
        "loan_categories": ["Education Loan"],
        "priority": QuestionPriority.CRITICAL_ELIGIBILITY.value,
        "question": "What is the total estimated funding required for tuition and living costs?",
        "explanation": "Includes university tuition fees, boarding, travel, and books. Repayment begins after completion of course + 6 to 12 months moratorium.",
        "input_type": "currency",
        "placeholder": "e.g. 35,00,000",
        "options": [
            {"label": "Up to ₹7.5 Lakhs (Unsecured)", "value": 750000},
            {"label": "₹15 – ₹30 Lakhs", "value": 2200000},
            {"label": "₹30 – ₹60 Lakhs", "value": 4500000},
            {"label": "₹60 Lakhs+", "value": 7500000}
        ],
        "allow_custom_input": True,
        "allow_skip": False,
        "decision_impacts": [
            {
                "impact_type": DecisionImpactType.AFFORDABILITY_ASSESSMENT.value,
                "affected_attribute": "education_repayment_capacity",
                "operation": "EVALUATE_EDUCATION_QUANTUM",
                "rule_description": "Determines co-borrower financial guarantee requirement based on requested quantum."
            }
        ]
    }
}

class DecisionCompletenessEngine:
    """
    Evaluates whether the profile has sufficient underwriting parameters to recommend loans,
    or whether targeted clarification questions must be asked first.
    Calculates Value of Information (VoI) and 3-Tier Recommendation Readiness.
    """

    def evaluate_readiness(
        self,
        profile: LoanDiscoveryProfile,
        intent: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determines whether the engine is ready to generate personalized recommendations,
        or what questions to ask next. Calculates 3-Tier Recommendation Readiness:
        - PRELIMINARY: Critical parameters unstated; cannot recommend responsibly.
        - PERSONALIZED: Core financial parameters known; can recommend with preference ranking.
        - ELIGIBILITY_ASSESSED: Full institutional criteria and collateral assessed.
        """
        # Non-discovery intents don't need discovery clarification
        if intent in ["GENERAL_EDUCATION", "CONCEPT_FAQ", "SPECIFIC_PRODUCT_QUERY"]:
            return {
                "ready_for_recommendation": True,
                "readiness": ReadinessLevel.ELIGIBILITY_ASSESSED.value,
                "readiness_label": "Informational Query Verified",
                "missing_critical_fields": [],
                "missing_important_fields": [],
                "known_dimensions": ["intent"],
                "next_questions": [],
                "discovery_progress": {
                    "readiness": ReadinessLevel.ELIGIBILITY_ASSESSED.value,
                    "readiness_label": "Informational Query Verified",
                    "known_count": 1,
                    "total_core_dimensions": 1
                }
            }

        q_lower = (query or "").lower()
        category = profile.loan_category.value or "Home Loan"
        is_ltv_query = any(k in q_lower for k in ["ltv", "loan to value", "property value", "purchase price", "margin money", "down payment"])

        missing_critical = []
        missing_important = []
        known_dimensions = []

        # ==================== DIMENSION AUDITING ====================
        # 1. Quantum
        if profile.requested_amount.is_known():
            known_dimensions.append("requested_amount")
        else:
            missing_critical.append("requested_amount")

        # 2. Category-Specific Critical Dimensions
        if category == "Home Loan":
            if is_ltv_query or profile.property_value.is_known():
                if profile.property_value.is_known():
                    known_dimensions.append("property_value")
                else:
                    missing_critical.append("property_value")

                if profile.property_type.is_known():
                    known_dimensions.append("property_type")
                else:
                    missing_critical.append("property_type")

            if profile.preferred_tenure_months.is_known():
                known_dimensions.append("preferred_tenure_months")
            else:
                missing_critical.append("preferred_tenure_months")

            if profile.monthly_net_income.is_known():
                known_dimensions.append("monthly_net_income")
            else:
                missing_critical.append("monthly_net_income")

            if profile.city.is_known():
                known_dimensions.append("city")
            else:
                missing_important.append("city")

        elif category == "Personal Loan":
            if profile.preferred_tenure_months.is_known():
                known_dimensions.append("preferred_tenure_months")
            else:
                missing_critical.append("preferred_tenure_months")

            if profile.monthly_net_income.is_known():
                known_dimensions.append("monthly_net_income")
            else:
                missing_critical.append("monthly_net_income")

            if profile.salary_bank.is_known():
                known_dimensions.append("salary_bank")
            else:
                missing_important.append("salary_bank")

        elif category == "Vehicle Loan":
            if profile.vehicle_type.is_known():
                known_dimensions.append("vehicle_type")
            else:
                missing_critical.append("vehicle_type")

            if profile.preferred_tenure_months.is_known():
                known_dimensions.append("preferred_tenure_months")
            else:
                missing_critical.append("preferred_tenure_months")

            if profile.monthly_net_income.is_known():
                known_dimensions.append("monthly_net_income")
            else:
                missing_important.append("monthly_net_income")

        elif category == "Education Loan":
            if profile.study_destination.is_known():
                known_dimensions.append("study_destination")
            else:
                missing_critical.append("study_destination")

            if profile.collateral_type.is_known():
                known_dimensions.append("collateral_type")
            else:
                missing_important.append("collateral_type")

            if profile.monthly_net_income.is_known():
                known_dimensions.append("monthly_net_income")
            else:
                missing_important.append("monthly_net_income")
        else:
            if profile.preferred_tenure_months.is_known():
                known_dimensions.append("preferred_tenure_months")
            else:
                missing_critical.append("preferred_tenure_months")

            if profile.monthly_net_income.is_known():
                known_dimensions.append("monthly_net_income")
            else:
                missing_critical.append("monthly_net_income")

        # 3. Universal Important Dimensions (Existing obligations, CIBIL, Priorities)
        if profile.existing_monthly_emi.is_known():
            known_dimensions.append("existing_monthly_emi")
        else:
            missing_important.append("existing_monthly_emi")

        if profile.employment_type.is_known():
            known_dimensions.append("employment_type")
        else:
            missing_important.append("employment_type")

        if profile.self_reported_credit_score.is_known() or profile.self_reported_credit_score.state == FieldState.DECLINED:
            known_dimensions.append("cibil_score")
        else:
            missing_important.append("cibil_score")

        # ==================== 3-TIER READINESS EVALUATION ====================
        if len(missing_critical) > 0:
            readiness = ReadinessLevel.PRELIMINARY
            readiness_label = f"Preliminary Discovery · {len(missing_critical)} Critical Details Missing"
            ready = False
        elif len(missing_important) > 1:
            readiness = ReadinessLevel.PERSONALIZED
            readiness_label = "Personalized Matching Ready · Key Criteria Established"
            ready = True
        else:
            readiness = ReadinessLevel.ELIGIBILITY_ASSESSED
            readiness_label = "Underwriting Assessed · Full Profile Verified"
            ready = True

        # ==================== DYNAMIC QUESTION SELECTION BY VOI ====================
        # Select the top 2-3 questions with the highest Value of Information (VoI)
        next_question_keys = []

        if is_ltv_query:
            if "property_value" in missing_critical:
                next_question_keys.append("PROPERTY_VALUE")
            if "property_type" in missing_critical:
                next_question_keys.append("PROPERTY_TYPE")
            if "city" in missing_important:
                next_question_keys.append("PROPERTY_LOCATION")
            if len(next_question_keys) < 3 and "monthly_net_income" in missing_critical:
                next_question_keys.append("MONTHLY_NET_INCOME")
        else:
            # 1. Critical questions for this loan category
            if category == "Home Loan":
                if "requested_amount" in missing_critical:
                    next_question_keys.append("HOME_LOAN_AMOUNT")
                if "preferred_tenure_months" in missing_critical:
                    next_question_keys.append("HOME_LOAN_TENURE")
                if "monthly_net_income" in missing_critical:
                    next_question_keys.append("MONTHLY_NET_INCOME")
            elif category == "Personal Loan":
                if "requested_amount" in missing_critical:
                    next_question_keys.append("PERSONAL_LOAN_AMOUNT")
                if "preferred_tenure_months" in missing_critical:
                    next_question_keys.append("PERSONAL_LOAN_TENURE")
                if "monthly_net_income" in missing_critical:
                    next_question_keys.append("MONTHLY_NET_INCOME")
                if len(next_question_keys) < 2 and "salary_bank" in missing_important:
                    next_question_keys.append("SALARY_CREDIT_BANK")
            elif category == "Vehicle Loan":
                if "vehicle_type" in missing_critical:
                    next_question_keys.append("VEHICLE_TYPE")
                if "requested_amount" in missing_critical:
                    next_question_keys.append("CAR_LOAN_AMOUNT")
                if "preferred_tenure_months" in missing_critical:
                    next_question_keys.append("CAR_LOAN_TENURE")
            elif category == "Education Loan":
                if "study_destination" in missing_critical:
                    next_question_keys.append("EDUCATION_DESTINATION")
                if "requested_amount" in missing_critical:
                    next_question_keys.append("EDUCATION_LOAN_AMOUNT")
                if len(next_question_keys) < 2 and "collateral_type" in missing_important:
                    next_question_keys.append("EDUCATION_COLLATERAL")
            else:
                if "requested_amount" in missing_critical:
                    next_question_keys.append("HOME_LOAN_AMOUNT")
                if "preferred_tenure_months" in missing_critical:
                    next_question_keys.append("HOME_LOAN_TENURE")
                if "monthly_net_income" in missing_critical:
                    next_question_keys.append("MONTHLY_NET_INCOME")

            # 2. Secondary Important Questions if slots available (<3)
            if len(next_question_keys) < 2 and "existing_monthly_emi" in missing_important:
                next_question_keys.append("EXISTING_MONTHLY_EMI")
            if len(next_question_keys) < 2 and "employment_type" in missing_important:
                next_question_keys.append("EMPLOYMENT_TYPE")
            if len(next_question_keys) < 3 and "cibil_score" in missing_important:
                next_question_keys.append("CIBIL_SCORE_TIER")
            if len(next_question_keys) < 3 and not profile.priorities:
                next_question_keys.append("BORROWER_PRIORITY")

        selected_questions = [QUESTION_BANK[k] for k in next_question_keys[:3] if k in QUESTION_BANK]

        total_dimensions = len(known_dimensions) + len(missing_critical) + len(missing_important)

        # Build educational summary
        amt_known = profile.requested_amount.is_known()
        amt_str = f"₹{profile.requested_amount.value:,.0f}" if amt_known else "your desired loan"

        if is_ltv_query:
            summary = (
                "To accurately assess your eligibility for a 90% Loan-to-Value (LTV) request under RBI guidelines, "
                "banks lend up to 90% only for loans up to ₹30 Lakhs, 80% up to ₹75 Lakhs, and 75% above ₹75 Lakhs "
                "for residential properties. Commercial properties and plots are capped at 60%–70% LTV."
            )
        else:
            summary = (
                f"To identify the most competitive, verified {category.lower()} options for {amt_str} "
                "without risking application rejection, Indian banks evaluate core underwriting factors under RBI guidelines."
            )

        return {
            "ready_for_recommendation": ready,
            "readiness": readiness.value,
            "readiness_label": readiness_label,
            "category": f"{category} LTV" if is_ltv_query else category,
            "completion_level": "COMPLETE" if ready and len(missing_important) == 0 else ("PARTIAL" if ready else "INSUFFICIENT"),
            "missing_critical_fields": missing_critical,
            "missing_important_fields": missing_important,
            "known_dimensions": known_dimensions,
            "next_questions": selected_questions,
            "educational_summary": summary,
            "discovery_progress": {
                "readiness": readiness.value,
                "readiness_label": readiness_label,
                "known_count": len(known_dimensions),
                "total_core_dimensions": total_dimensions,
                "percentage": round((len(known_dimensions) / max(1, total_dimensions)) * 100)
            }
        }

# Backward compatible alias
ClarificationManager = DecisionCompletenessEngine
