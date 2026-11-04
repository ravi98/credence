from enum import Enum
from typing import Optional, List, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class ProvenanceSource(str, Enum):
    USER_PROVIDED = "USER_PROVIDED"
    EXISTING_PROFILE = "EXISTING_PROFILE"
    EXTERNAL_VERIFIED = "EXTERNAL_VERIFIED"
    SYSTEM_CALCULATED = "SYSTEM_CALCULATED"
    INFERRED_UNCONFIRMED = "INFERRED_UNCONFIRMED"
    UNKNOWN = "UNKNOWN"
    DECLINED = "DECLINED"

class FieldState(str, Enum):
    KNOWN = "KNOWN"
    INFERRED_UNCONFIRMED = "INFERRED_UNCONFIRMED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    DECLINED = "DECLINED"

class FieldItem(BaseModel, Generic[T]):
    value: Optional[T] = None
    source: ProvenanceSource = ProvenanceSource.UNKNOWN
    state: FieldState = FieldState.UNKNOWN
    confirmed: bool = False

    def set_user_value(self, val: T):
        self.value = val
        self.source = ProvenanceSource.USER_PROVIDED
        self.state = FieldState.KNOWN
        self.confirmed = True

    def set_inferred(self, val: T):
        self.value = val
        self.source = ProvenanceSource.INFERRED_UNCONFIRMED
        self.state = FieldState.INFERRED_UNCONFIRMED
        self.confirmed = False

    def is_known(self) -> bool:
        return self.state == FieldState.KNOWN and self.value is not None

class LoanCategory(str, Enum):
    HOME_LOAN = "Home Loan"
    PERSONAL_LOAN = "Personal Loan"
    EDUCATION_LOAN = "Education Loan"
    VEHICLE_LOAN = "Vehicle Loan"
    BUSINESS_LOAN = "Business Loan"

class LoanDiscoveryProfile(BaseModel):
    version: int = 1

    # A. Loan Requirements
    loan_category: FieldItem[str] = Field(default_factory=lambda: FieldItem[str](value="Home Loan", state=FieldState.KNOWN, source=ProvenanceSource.USER_PROVIDED))
    loan_purpose: FieldItem[str] = Field(default_factory=FieldItem[str])
    requested_amount: FieldItem[float] = Field(default_factory=FieldItem[float]) # In Rupees
    preferred_tenure_months: FieldItem[int] = Field(default_factory=FieldItem[int])
    city: FieldItem[str] = Field(default_factory=FieldItem[str])
    preferred_lender_type: FieldItem[str] = Field(default_factory=FieldItem[str]) # Public, Private, NBFC

    # B. Employment & Income
    employment_type: FieldItem[str] = Field(default_factory=FieldItem[str]) # Salaried, Self-Employed, etc.
    company_name: FieldItem[str] = Field(default_factory=FieldItem[str])
    monthly_net_income: FieldItem[float] = Field(default_factory=FieldItem[float]) # In Rupees
    existing_monthly_emi: FieldItem[float] = Field(default_factory=FieldItem[float]) # In Rupees

    # C. Credit Profile
    self_reported_credit_score: FieldItem[int] = Field(default_factory=FieldItem[int])
    credit_score_range: FieldItem[str] = Field(default_factory=FieldItem[str]) # 750+, 700-749, <700

    # D. Repayment & Financial Priorities
    comfortable_monthly_emi: FieldItem[float] = Field(default_factory=FieldItem[float])
    maximum_monthly_emi: FieldItem[float] = Field(default_factory=FieldItem[float])
    fixed_or_floating_preference: FieldItem[str] = Field(default_factory=FieldItem[str]) # Floating (EBLR), Fixed
    priorities: List[str] = Field(default_factory=list) # LOWEST_TOTAL_INTEREST, LOWER_MONTHLY_EMI, FAST_PROCESSING, LOW_FEES

    # Category-specific fields
    property_type: FieldItem[str] = Field(default_factory=FieldItem[str])
    property_value: FieldItem[float] = Field(default_factory=FieldItem[float])
    down_payment: FieldItem[float] = Field(default_factory=FieldItem[float])
    vehicle_type: FieldItem[str] = Field(default_factory=FieldItem[str]) # "New", "Used"
    study_destination: FieldItem[str] = Field(default_factory=FieldItem[str]) # "Domestic", "Overseas"
    collateral_type: FieldItem[str] = Field(default_factory=FieldItem[str]) # "Unsecured / Collateral-Free", "Immovable Property Collateral"
    salary_bank: FieldItem[str] = Field(default_factory=FieldItem[str])

    def to_dict_summary(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "loan_category": self.loan_category.value,
            "requested_amount": self.requested_amount.value,
            "preferred_tenure_months": self.preferred_tenure_months.value,
            "monthly_net_income": self.monthly_net_income.value,
            "existing_monthly_emi": self.existing_monthly_emi.value,
            "employment_type": self.employment_type.value,
            "cibil_score": self.self_reported_credit_score.value,
            "city": self.city.value,
            "priorities": self.priorities,
            "maximum_monthly_emi": self.maximum_monthly_emi.value,
            "property_type": self.property_type.value,
            "property_value": self.property_value.value,
            "down_payment": self.down_payment.value,
            "vehicle_type": self.vehicle_type.value,
            "study_destination": self.study_destination.value,
            "collateral_type": self.collateral_type.value,
            "salary_bank": self.salary_bank.value
        }

    @classmethod
    def from_dict_summary(cls, d: Dict[str, Any]) -> "LoanDiscoveryProfile":
        p = cls(version=d.get("version", 1))
        if d.get("loan_category"):
            p.loan_category.set_user_value(d["loan_category"])
        if d.get("requested_amount") is not None:
            p.requested_amount.set_user_value(float(d["requested_amount"]))
        if d.get("preferred_tenure_months") is not None:
            p.preferred_tenure_months.set_user_value(int(d["preferred_tenure_months"]))
        if d.get("monthly_net_income") is not None:
            p.monthly_net_income.set_user_value(float(d["monthly_net_income"]))
        if d.get("existing_monthly_emi") is not None:
            p.existing_monthly_emi.set_user_value(float(d["existing_monthly_emi"]))
        if d.get("employment_type"):
            p.employment_type.set_user_value(d["employment_type"])
        if d.get("cibil_score") is not None:
            p.self_reported_credit_score.set_user_value(int(d["cibil_score"]))
        if d.get("city"):
            p.city.set_user_value(d["city"])
        if d.get("priorities"):
            p.priorities = list(d["priorities"])
        if d.get("maximum_monthly_emi") is not None:
            p.maximum_monthly_emi.set_user_value(float(d["maximum_monthly_emi"]))
        if d.get("property_type"):
            p.property_type.set_user_value(d["property_type"])
        if d.get("property_value") is not None:
            p.property_value.set_user_value(float(d["property_value"]))
        if d.get("down_payment") is not None:
            p.down_payment.set_user_value(float(d["down_payment"]))
        if d.get("vehicle_type"):
            p.vehicle_type.set_user_value(d["vehicle_type"])
        if d.get("study_destination"):
            p.study_destination.set_user_value(d["study_destination"])
        if d.get("collateral_type"):
            p.collateral_type.set_user_value(d["collateral_type"])
        if d.get("salary_bank"):
            p.salary_bank.set_user_value(d["salary_bank"])
        return p


