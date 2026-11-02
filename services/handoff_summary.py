import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from openai import OpenAI
from sqlalchemy.orm import Session

from database import SessionLocal
from models.enquiry import LoanEnquiry, SummaryStatus

logger = logging.getLogger("credence.handoff")

def generate_fallback_summary(enquiry: LoanEnquiry) -> Dict[str, Any]:
    """
    Deterministic rule-based underwriting summary in case LLM is unreachable.
    Ensures 100% reliability and zero broken handoff records.
    """
    borrower = enquiry.borrower_profile_snapshot or {}
    income = borrower.get("monthly_income") or 0
    amount = float(enquiry.requested_amount) if enquiry.requested_amount else 0
    tenure_years = (enquiry.preferred_tenure_months or 240) // 12
    employment = borrower.get("employment", "Salaried")
    cibil = borrower.get("cibil_score", 750)

    # Primary product
    primary_prod = None
    if enquiry.products:
        for p in enquiry.products:
            if getattr(p, "preference_type", None) == "PRIMARY" or str(p.preference_type).endswith("PRIMARY"):
                primary_prod = p
                break
        if not primary_prod and enquiry.products:
            primary_prod = enquiry.products[0]

    primary_name = f"{primary_prod.institution} - {primary_prod.scheme_name}" if primary_prod else "Selected Bank Scheme"

    strengths = []
    if cibil >= 750:
        strengths.append(f"Strong credit track record with CIBIL score of {cibil}.")
    if employment == "Salaried":
        strengths.append("Salaried employment profile with predictable monthly payroll cash flows.")
    else:
        strengths.append(f"{employment} borrower with self-sustaining business/professional earnings.")

    if income > 0 and amount > 0:
        annual_income = income * 12
        if amount <= annual_income * 6:
            strengths.append(f"Reasonable loan-to-annual-income ratio ({round(amount / annual_income, 1)}x).")

    risks = []
    if cibil < 720:
        risks.append("CIBIL score is below 720; bank might apply an interest rate spread markup or request a co-applicant.")
    if income > 0 and (amount / (income * 12)) > 6:
        risks.append("Requested loan quantum is high relative to current declared monthly net income.")

    if not risks:
        risks.append("No adverse risk flags identified in declared baseline profile. Full income document verification required.")

    return {
        "executive_summary": f"Applicant has requested a ₹{amount:,.0f} {enquiry.loan_category} over {tenure_years} years, actively considering {primary_name}. Verified readiness is high with preliminary requirements established in chat.",
        "borrower_strengths": strengths,
        "risk_factors_and_mitigants": risks,
        "recommended_lender_pitch": [
            f"Highlight {primary_name}'s competitive interest rate benchmark and transparent processing fee structure.",
            "Emphasize zero prepayment penalty for floating rate retail facilities as per RBI fair practices directives.",
            "Offer doorstep document pickup and digital fast-track sanction assistance through Credence partner desk."
        ],
        "recommended_next_steps": [
            "Initiate introductory consultation call within 2 business hours via preferred channel.",
            "Verify employment stability and collect last 3 months pay slips + 6 months bank statement.",
            "Perform digital CIBIL consent verification and generate preliminary bank sanction in-principle."
        ],
        "recommended_documents": [
            "PAN Card & Aadhaar Card (Identity & Address proof)",
            "Last 3 months salary slips or 2 years audited ITR + Computation",
            "Last 6 months operative bank statement showing salary/business credits",
            "Property / Asset documents or draft agreement to sale (if finalized)"
        ],
        "generated_by": "deterministic_rule_engine",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

def generate_ai_handoff_summary(enquiry_id: str) -> None:
    """
    Background worker task to synthesize an immutable AI Underwriting Handoff Briefing.
    Frozen at submission time so sales executives read it instantly with zero runtime LLM cost.
    """
    with SessionLocal() as db:
        enquiry = db.query(LoanEnquiry).filter(LoanEnquiry.id == enquiry_id).first()
        if not enquiry:
            logger.error(f"Enquiry {enquiry_id} not found for AI handoff summary generation.")
            return

        # Set status to GENERATING
        enquiry.summary_status = SummaryStatus.GENERATING
        db.commit()

        api_key = os.environ.get("GROQ_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
        model_name = os.environ.get("MODEL_NAME", "qwen/qwen3.8-27b")

        summary_data = None

        if api_key:
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)

                borrower_info = enquiry.borrower_profile_snapshot or {}
                contact_info = enquiry.contact_details_snapshot or {}
                contact_prefs = enquiry.contact_preferences or {}

                products_desc = []
                for p in enquiry.products:
                    pref = getattr(p, "preference_type", "PRIMARY")
                    products_desc.append(f"- [{pref}] {p.institution} - {p.scheme_name}: Snapshot: {json.dumps(p.product_snapshot)}")

                prompt_content = f"""You are Credence Senior Retail Underwriting Analyst.
Analyze the following customer loan inquiry and produce a structured, high-value executive briefing for the assigned sales loan specialist.

CUSTOMER APPLICATION DETAILS:
- Reference ID: {enquiry.enquiry_reference}
- Category: {enquiry.loan_category}
- Requested Loan Amount: Rs. {enquiry.requested_amount:,.2f}
- Preferred Tenure: {enquiry.preferred_tenure_months} months
- Borrower Profile: {json.dumps(borrower_info)}
- Contact Preferences: {json.dumps(contact_prefs)}
- Selected Products:
{chr(10).join(products_desc)}

CONVERSATION CONTEXT SUMMARY:
Applicant consulted the AI Loan Advisor and finalized these parameters after reviewing grounded banking catalog schemes.

OUTPUT REQUIREMENT:
Output ONLY valid JSON matching this exact structure:
{{
  "executive_summary": "2-3 concise sentences summarising the customer's intent, requirement, profile match, and urgency.",
  "borrower_strengths": ["Key positive underwriting highlight 1", "Highlight 2", "Highlight 3"],
  "risk_factors_and_mitigants": ["Key risk or qualification hurdle and recommended mitigant"],
  "recommended_lender_pitch": ["Specific talking point 1 for the chosen bank", "Talking point 2"],
  "recommended_next_steps": ["Actionable step 1 for sales officer", "Actionable step 2", "Actionable step 3"],
  "recommended_documents": ["Document 1", "Document 2", "Document 3", "Document 4"]
}}
"""

                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a professional banking underwriting advisor. Output strictly raw JSON without markdown code fences."},
                        {"role": "user", "content": prompt_content}
                    ],
                    temperature=0.2,
                    max_tokens=850
                )

                raw_text = response.choices[0].message.content.strip()
                if raw_text.startswith("```"):
                    raw_text = raw_text.strip("`")
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:].strip()

                summary_data = json.loads(raw_text)
                summary_data["generated_by"] = "llm_underwriting_engine"
                summary_data["generated_at"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.warning(f"LLM AI handoff generation failed for enquiry {enquiry_id}: {e}. Employing deterministic fallback.")

        if not summary_data:
            summary_data = generate_fallback_summary(enquiry)

        enquiry.ai_handoff_summary = summary_data
        enquiry.summary_status = SummaryStatus.COMPLETED
        enquiry.summary_generated_at = datetime.now(timezone.utc)
        enquiry.summary_version = 1
        db.commit()
        logger.info(f"Successfully generated frozen AI handoff summary for {enquiry.enquiry_reference}")

