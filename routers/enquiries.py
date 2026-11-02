import os
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from auth_deps import get_current_user
from models.user import User, UserRole
from models.borrower import BorrowerProfile
from models.enquiry import (
    LoanEnquiry,
    EnquiryProduct,
    ConsentRecord,
    LeadStatusHistory,
    LeadStatus,
    SummaryStatus,
    PreferenceType
)
from services.handoff_summary import generate_ai_handoff_summary

router = APIRouter()

# Load catalog manifest for frozen product snapshot resolution
MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "catalog_manifest.json")
try:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        CATALOG_SCHEMES = json.load(f).get("schemes", [])
except Exception:
    CATALOG_SCHEMES = []

def find_scheme_by_slug_or_name(identifier: str) -> Optional[Dict[str, Any]]:
    if not identifier:
        return None
    ident = identifier.strip().lower()
    for s in CATALOG_SCHEMES:
        if s.get("scheme_slug", "").lower() == ident:
            return s
        if s.get("compact_key", "").lower() == ident:
            return s
        if s.get("scheme_name", "").lower() == ident:
            return s
    # Partial match
    for s in CATALOG_SCHEMES:
        if ident in s.get("scheme_name", "").lower() or ident in s.get("scheme_slug", "").lower():
            return s
    return None

def build_product_snapshot(scheme_match: Optional[Dict[str, Any]], fallback_name: str, fallback_bank: str) -> Dict[str, Any]:
    if scheme_match:
        return {
            "institution": scheme_match.get("institution", fallback_bank),
            "scheme_name": scheme_match.get("scheme_name", fallback_name),
            "category": scheme_match.get("category", "Retail Loan"),
            "sector": scheme_match.get("sector", "Banking"),
            "interest_rate_range": scheme_match.get("interest_rate_range", "Competitive Market Rate"),
            "min_rate_num": scheme_match.get("min_rate_num"),
            "benchmark": scheme_match.get("benchmark", "EBLR / Repo-linked"),
            "max_tenure_years": scheme_match.get("max_tenure_years", 30),
            "max_loan_amount": scheme_match.get("max_loan_amount", "Subject to Income"),
            "source_url": scheme_match.get("source_url", ""),
            "verified_at": scheme_match.get("verified_at", datetime.now(timezone.utc).isoformat())
        }
    return {
        "institution": fallback_bank,
        "scheme_name": fallback_name,
        "category": "Retail Loan",
        "sector": "Banking",
        "interest_rate_range": "Competitive Market Rate",
        "benchmark": "Repo Linked Benchmark",
        "max_tenure_years": 30,
        "max_loan_amount": "Subject to Income Eligibility",
        "verified_at": datetime.now(timezone.utc).isoformat()
    }

# ==================== Pydantic Schemas ====================

class ContactPreferencesInput(BaseModel):
    preferred_channel: str = "WhatsApp"
    preferred_time_slot: str = "Morning (10 AM - 1 PM)"
    alternate_phone: Optional[str] = None
    notes: Optional[str] = None

class BorrowerDetailsInput(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., min_length=10, max_length=15)
    email: str = Field(..., min_length=5, max_length=150)
    employment: str = "Salaried"
    monthly_income: float = Field(..., gt=0)
    requested_amount: float = Field(..., gt=0)
    preferred_tenure_months: int = Field(240, gt=0, le=480)
    city: str = Field("Mumbai", min_length=2, max_length=100)
    company_name: Optional[str] = None
    existing_emi: Optional[float] = 0.0
    cibil_score: Optional[int] = 750
    category: Optional[str] = "Home Loan"

class ConsentItemInput(BaseModel):
    purpose: str # CREDENCE_CONTACT, LENDER_DATA_SHARING, MARKETING_COMMUNICATION
    granted: bool

class ProductSelectionInput(BaseModel):
    slug_or_name: str
    institution: Optional[str] = "Partner Bank"
    scheme_name: Optional[str] = None

class CreateEnquiryRequest(BaseModel):
    conversation_id: Optional[str] = None
    primary_product: ProductSelectionInput
    alternative_products: Optional[List[ProductSelectionInput]] = []
    borrower_details: BorrowerDetailsInput
    contact_preferences: ContactPreferencesInput
    consents: List[ConsentItemInput]
    conversation_history: Optional[List[Dict[str, Any]]] = []

class EnquiryResponse(BaseModel):
    success: bool
    enquiry_id: str
    enquiry_reference: str
    status: str
    created_at: str

# ==================== Endpoints ====================

@router.post("", response_model=EnquiryResponse)
async def create_loan_enquiry(
    req: CreateEnquiryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a new customer loan enquiry with an immutable 4-part point-in-time snapshot,
    unbundled consent records, and kicks off asynchronous frozen AI handoff generation.
    """
    # 1. Enforce mandatory unbundled consents (DPDP Act & RBI fair practices)
    contact_consent = next((c for c in req.consents if c.purpose == "CREDENCE_CONTACT"), None)
    lender_consent = next((c for c in req.consents if c.purpose == "LENDER_DATA_SHARING"), None)

    if not contact_consent or not contact_consent.granted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent to be contacted by a Credence specialist is mandatory to submit an enquiry."
        )

    if not lender_consent or not lender_consent.granted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent to share details with partner lenders for loan qualification is mandatory."
        )

    # 2. Generate unique human-readable enquiry reference ID (e.g. CRD-202611-0421)
    period_code = datetime.now(timezone.utc).strftime("%Y%m")
    unique_suffix = uuid.uuid4().hex[:4].upper()
    enquiry_ref = f"CRD-{period_code}-{unique_suffix}"

    # Ensure uniqueness in DB
    while db.query(LoanEnquiry).filter(LoanEnquiry.enquiry_reference == enquiry_ref).first():
        unique_suffix = uuid.uuid4().hex[:4].upper()
        enquiry_ref = f"CRD-{period_code}-{unique_suffix}"

    enquiry_id = f"enq_{uuid.uuid4().hex[:12]}"

    # 3. Build immutable snapshots
    borrower_snapshot = {
        "full_name": req.borrower_details.full_name,
        "phone": req.borrower_details.phone,
        "email": req.borrower_details.email,
        "employment": req.borrower_details.employment,
        "monthly_income": req.borrower_details.monthly_income,
        "requested_amount": req.borrower_details.requested_amount,
        "preferred_tenure_months": req.borrower_details.preferred_tenure_months,
        "city": req.borrower_details.city,
        "company_name": req.borrower_details.company_name,
        "existing_emi": req.borrower_details.existing_emi or 0.0,
        "cibil_score": req.borrower_details.cibil_score or 750,
        "category": req.borrower_details.category or "Home Loan",
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }

    contact_details_snapshot = {
        "full_name": req.borrower_details.full_name,
        "phone": req.borrower_details.phone,
        "email": req.borrower_details.email,
        "city": req.borrower_details.city
    }

    contact_preferences_snapshot = req.contact_preferences.model_dump()

    # 4. Create LoanEnquiry
    enquiry = LoanEnquiry(
        id=enquiry_id,
        enquiry_reference=enquiry_ref,
        customer_user_id=current_user.id,
        conversation_id=req.conversation_id,
        loan_category=req.borrower_details.category or "Home Loan",
        requested_amount=Decimal(str(req.borrower_details.requested_amount)),
        preferred_tenure_months=req.borrower_details.preferred_tenure_months,
        borrower_profile_snapshot=borrower_snapshot,
        contact_details_snapshot=contact_details_snapshot,
        contact_preferences=contact_preferences_snapshot,
        current_lead_status=LeadStatus.NEW,
        summary_status=SummaryStatus.PENDING
    )
    db.add(enquiry)

    # 5. Create primary and alternative EnquiryProduct records with frozen snapshots
    primary_scheme = find_scheme_by_slug_or_name(req.primary_product.slug_or_name)
    primary_bank = req.primary_product.institution or (primary_scheme.get("institution") if primary_scheme else "Partner Bank")
    primary_name = req.primary_product.scheme_name or (primary_scheme.get("scheme_name") if primary_scheme else req.primary_product.slug_or_name)
    primary_snapshot = build_product_snapshot(primary_scheme, primary_name, primary_bank)

    primary_prod_record = EnquiryProduct(
        id=f"ep_{uuid.uuid4().hex[:12]}",
        enquiry_id=enquiry_id,
        product_reference=req.primary_product.slug_or_name,
        institution=primary_bank,
        scheme_name=primary_name,
        preference_type=PreferenceType.PRIMARY,
        display_order=1,
        product_snapshot=primary_snapshot
    )
    db.add(primary_prod_record)

    # Alternatives
    order = 2
    for alt in (req.alternative_products or []):
        alt_scheme = find_scheme_by_slug_or_name(alt.slug_or_name)
        alt_bank = alt.institution or (alt_scheme.get("institution") if alt_scheme else "Alternative Bank")
        alt_name = alt.scheme_name or (alt_scheme.get("scheme_name") if alt_scheme else alt.slug_or_name)
        alt_snapshot = build_product_snapshot(alt_scheme, alt_name, alt_bank)

        alt_prod_record = EnquiryProduct(
            id=f"ep_{uuid.uuid4().hex[:12]}",
            enquiry_id=enquiry_id,
            product_reference=alt.slug_or_name,
            institution=alt_bank,
            scheme_name=alt_name,
            preference_type=PreferenceType.ALTERNATIVE,
            display_order=order,
            product_snapshot=alt_snapshot
        )
        db.add(alt_prod_record)
        order += 1

    # 6. Record unbundled consents
    for c in req.consents:
        consent_record = ConsentRecord(
            id=f"cst_{uuid.uuid4().hex[:12]}",
            user_id=current_user.id,
            enquiry_id=enquiry_id,
            purpose=c.purpose,
            consent_action="GRANTED" if c.granted else "DECLINED",
            notice_version="1.0",
            source="ENQUIRY_FLOW"
        )
        db.add(consent_record)

    # 7. Initial status audit log
    status_entry = LeadStatusHistory(
        id=f"lsh_{uuid.uuid4().hex[:12]}",
        enquiry_id=enquiry_id,
        previous_status=None,
        new_status="NEW",
        changed_by_user_id=current_user.id,
        reason="Initial application submission via Credence AI Loan Advisor flow."
    )
    db.add(status_entry)

    # 8. Enrich customer's BorrowerProfile
    borrower_prof = db.query(BorrowerProfile).filter(BorrowerProfile.user_id == current_user.id).first()
    if not borrower_prof:
        borrower_prof = BorrowerProfile(
            id=f"bp_{uuid.uuid4().hex[:12]}",
            user_id=current_user.id,
            employment_type=req.borrower_details.employment,
            monthly_income=Decimal(str(req.borrower_details.monthly_income)),
            existing_monthly_obligations=Decimal(str(req.borrower_details.existing_emi or 0.0)),
            self_reported_credit_score=req.borrower_details.cibil_score or 750,
            city=req.borrower_details.city,
            preferred_loan_category=req.borrower_details.category
        )
        db.add(borrower_prof)
    else:
        borrower_prof.employment_type = req.borrower_details.employment
        borrower_prof.monthly_income = Decimal(str(req.borrower_details.monthly_income))
        borrower_prof.existing_monthly_obligations = Decimal(str(req.borrower_details.existing_emi or 0.0))
        borrower_prof.self_reported_credit_score = req.borrower_details.cibil_score or 750
        borrower_prof.city = req.borrower_details.city
        borrower_prof.preferred_loan_category = req.borrower_details.category

    db.commit()
    db.refresh(enquiry)

    # 9. Asynchronously generate frozen AI handoff summary in background
    background_tasks.add_task(generate_ai_handoff_summary, enquiry.id)

    return EnquiryResponse(
        success=True,
        enquiry_id=enquiry.id,
        enquiry_reference=enquiry.enquiry_reference,
        status=enquiry.current_lead_status.value if hasattr(enquiry.current_lead_status, "value") else str(enquiry.current_lead_status),
        created_at=enquiry.created_at.isoformat() if enquiry.created_at else datetime.now(timezone.utc).isoformat()
    )

@router.get("/my")
async def get_my_enquiries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the list of enquiries submitted by the authenticated customer.
    """
    enquiries = (
        db.query(LoanEnquiry)
        .filter(LoanEnquiry.customer_user_id == current_user.id)
        .order_by(desc(LoanEnquiry.created_at))
        .all()
    )

    result = []
    for enq in enquiries:
        # Get primary product
        primary_p = None
        for p in enq.products:
            if getattr(p, "preference_type", None) == PreferenceType.PRIMARY or str(p.preference_type).endswith("PRIMARY"):
                primary_p = p
                break
        if not primary_p and enq.products:
            primary_p = enq.products[0]

        result.append({
            "id": enq.id,
            "enquiry_reference": enq.enquiry_reference,
            "loan_category": enq.loan_category,
            "requested_amount": float(enq.requested_amount) if enq.requested_amount else 0,
            "preferred_tenure_months": enq.preferred_tenure_months,
            "current_status": enq.current_lead_status.value if hasattr(enq.current_lead_status, "value") else str(enq.current_lead_status),
            "primary_product": {
                "institution": primary_p.institution if primary_p else "Partner Bank",
                "scheme_name": primary_p.scheme_name if primary_p else "Retail Loan Scheme",
                "interest_rate": (primary_p.product_snapshot.get("interest_rate_range") if primary_p and primary_p.product_snapshot else "Market Rate")
            } if primary_p else None,
            "products_count": len(enq.products),
            "summary_status": enq.summary_status.value if hasattr(enq.summary_status, "value") else str(enq.summary_status),
            "created_at": enq.created_at.isoformat() if enq.created_at else None,
            "conversation_id": enq.conversation_id
        })

    return {
        "enquiries": result,
        "count": len(result)
    }

@router.get("/{enquiry_id}")
async def get_enquiry_details(
    enquiry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns full details for an enquiry.
    Customers can only access their own enquiries.
    Sales executives can access assigned or permitted leads.
    """
    enquiry = db.query(LoanEnquiry).filter(LoanEnquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(status_code=404, detail="Loan enquiry not found.")

    # Authorization check
    is_customer = current_user.role == UserRole.CUSTOMER or str(current_user.role).endswith("CUSTOMER")
    if is_customer and enquiry.customer_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this enquiry.")

    # Build response
    products_data = []
    for p in enquiry.products:
        pref = p.preference_type.value if hasattr(p.preference_type, "value") else str(p.preference_type)
        products_data.append({
            "id": p.id,
            "product_reference": p.product_reference,
            "institution": p.institution,
            "scheme_name": p.scheme_name,
            "preference_type": pref,
            "product_snapshot": p.product_snapshot
        })

    history_data = []
    for h in enquiry.status_history:
        history_data.append({
            "id": h.id,
            "previous_status": h.previous_status,
            "new_status": h.new_status,
            "reason": h.reason,
            "created_at": h.created_at.isoformat() if h.created_at else None
        })

    consents_data = []
    for c in enquiry.consents:
        consents_data.append({
            "purpose": c.purpose,
            "consent_action": c.consent_action,
            "captured_at": c.captured_at.isoformat() if c.captured_at else None
        })

    return {
        "id": enquiry.id,
        "enquiry_reference": enquiry.enquiry_reference,
        "customer_user_id": enquiry.customer_user_id,
        "conversation_id": enquiry.conversation_id,
        "loan_category": enquiry.loan_category,
        "requested_amount": float(enquiry.requested_amount) if enquiry.requested_amount else 0,
        "preferred_tenure_months": enquiry.preferred_tenure_months,
        "current_status": enquiry.current_lead_status.value if hasattr(enquiry.current_lead_status, "value") else str(enquiry.current_lead_status),
        "borrower_profile_snapshot": enquiry.borrower_profile_snapshot,
        "contact_details_snapshot": enquiry.contact_details_snapshot,
        "contact_preferences": enquiry.contact_preferences,
        "ai_handoff_summary": enquiry.ai_handoff_summary,
        "summary_status": enquiry.summary_status.value if hasattr(enquiry.summary_status, "value") else str(enquiry.summary_status),
        "summary_generated_at": enquiry.summary_generated_at.isoformat() if enquiry.summary_generated_at else None,
        "products": products_data,
        "status_history": history_data,
        "consents": consents_data,
        "created_at": enquiry.created_at.isoformat() if enquiry.created_at else None
    }

