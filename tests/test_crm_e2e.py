import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from server import app
import auth
from database import SessionLocal
from models.user import User, UserRole
from models.enquiry import LoanEnquiry, LeadStatus, ApplicationStatus

client = TestClient(app)

def test_full_crm_lifecycle():
    print("\n========== STARTING FULL CREDENCE CRM E2E TEST ==========")
    
    # Setup test users in DB
    with SessionLocal() as db:
        # Customer
        cust_email = f"e2e_cust_{uuid.uuid4().hex[:6]}@example.com"
        cust = auth.create_user(
            email=cust_email,
            name="Aarav Mehra",
            password="customerPassword123",
            role=UserRole.CUSTOMER,
            db=db
        )
        cust_id, cust_email_val, cust_name = cust.id, cust.email, cust.name
        
        # Sales Manager
        mgr_email = f"e2e_mgr_{uuid.uuid4().hex[:6]}@credence.in"
        mgr = auth.create_user(
            email=mgr_email,
            name="Vikram Malhotra (Lead Underwriter)",
            password="managerPassword123",
            role=UserRole.SALES_MANAGER,
            db=db
        )
        mgr_id, mgr_email_val, mgr_name = mgr.id, mgr.email, mgr.name

        # Sales Executive
        exec_email = f"e2e_exec_{uuid.uuid4().hex[:6]}@credence.in"
        exec_user = auth.create_user(
            email=exec_email,
            name="Priya Nair (Sales Specialist)",
            password="execPassword123",
            role=UserRole.SALES_EXECUTIVE,
            db=db
        )
        exec_id, exec_email_val, exec_name = exec_user.id, exec_user.email, exec_user.name

    # Step 1: Customer Auth
    res = client.post("/api/auth/login", json={"email": cust_email_val, "password": "customerPassword123"})
    assert res.status_code == 200, res.text
    cust_token = res.json()["token"]
    print(f"✓ Step 1: Customer '{cust_name}' authenticated.")

    # Step 2: Customer Submits Enquiry
    enquiry_payload = {
        "conversation_id": "chat_session_881",
        "primary_product": {
            "slug_or_name": "sbi-regular-home-loan",
            "institution": "State Bank of India",
            "scheme_name": "SBI Regular Home Loan"
        },
        "alternative_products": [
            {
                "slug_or_name": "hdfc-home-loan",
                "institution": "HDFC Bank",
                "scheme_name": "HDFC Standard Home Loan"
            }
        ],
        "borrower_details": {
            "full_name": "Aarav Mehra",
            "phone": "9820011223",
            "email": cust_email_val,
            "employment": "Salaried",
            "monthly_income": 120000,
            "requested_amount": 6500000,
            "preferred_tenure_months": 240,
            "city": "Mumbai",
            "company_name": "Tata Consultancy Services",
            "existing_emi": 15000,
            "cibil_score": 790,
            "category": "Home Loan"
        },
        "contact_preferences": {
            "preferred_channel": "WhatsApp",
            "preferred_time_slot": "Morning (10 AM - 1 PM)",
            "notes": "Looking for minimal processing fee and quick sanction."
        },
        "consents": [
            { "purpose": "CREDENCE_CONTACT", "granted": True },
            { "purpose": "LENDER_DATA_SHARING", "granted": True },
            { "purpose": "MARKETING_COMMUNICATION", "granted": True }
        ]
    }

    res = client.post("/api/enquiries", json=enquiry_payload, headers={"Authorization": f"Bearer {cust_token}"})
    assert res.status_code == 200, res.text
    enq_data = res.json()
    enquiry_id = enq_data["enquiry_id"]
    ref_id = enq_data["enquiry_reference"]
    assert enq_data["status"] == "NEW"
    print(f"✓ Step 2: Enquiry submitted with reference {ref_id}.")

    # Step 3: Verify Asynchronous AI Handoff Summary
    with SessionLocal() as db:
        enquiry = db.query(LoanEnquiry).filter(LoanEnquiry.id == enquiry_id).first()
        assert enquiry.summary_status.value == "COMPLETED"
        assert enquiry.ai_handoff_summary is not None
        summary = enquiry.ai_handoff_summary
        assert "executive_summary" in summary
        assert len(summary.get("borrower_strengths", [])) > 0
        assert len(summary.get("risk_factors_and_mitigants", [])) > 0
        print(f"✓ Step 3: Frozen AI Underwriting Briefing generated (Length of strengths: {len(summary['borrower_strengths'])}).")

    # Step 4: Customer checks My Enquiries
    res = client.get("/api/enquiries/my", headers={"Authorization": f"Bearer {cust_token}"})
    assert res.status_code == 200, res.text
    my_list = res.json()["enquiries"]
    assert any(e["enquiry_reference"] == ref_id for e in my_list)
    print(f"✓ Step 4: Customer sees enquiry {ref_id} in My Enquiries.")

    # Step 5: Customer attempting Sales access gets 403 Forbidden
    res = client.get("/api/sales/dashboard", headers={"Authorization": f"Bearer {cust_token}"})
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"
    print("✓ Step 5: Security gate verified — Customer blocked from sales endpoints (403 Forbidden).")

    # Step 6: Sales Manager logs in and views Inbox
    res = client.post("/api/auth/login", json={"email": mgr_email_val, "password": "managerPassword123"})
    assert res.status_code == 200, res.text
    mgr_token = res.json()["token"]

    res = client.get("/api/sales/leads", headers={"Authorization": f"Bearer {mgr_token}"})
    assert res.status_code == 200, res.text
    leads = res.json()["leads"]
    target_lead = next((l for l in leads if l["id"] == enquiry_id), None)
    assert target_lead is not None
    print(f"✓ Step 6: Manager '{mgr_name}' views new lead in inbox.")

    # Step 7: Sales Manager assigns lead to Priya Nair
    res = client.post(
        f"/api/sales/leads/{enquiry_id}/assign",
        json={
            "assigned_to_user_id": exec_id,
            "assignment_reason": "Top salaried customer in Mumbai, assigned for same-day contact."
        },
        headers={"Authorization": f"Bearer {mgr_token}"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["current_status"] == "ASSIGNED"
    print(f"✓ Step 7: Lead assigned to '{exec_name}'. Status transitioned to ASSIGNED.")

    # Step 8: Sales Executive Priya logs in and opens Workspace
    res = client.post("/api/auth/login", json={"email": exec_email_val, "password": "execPassword123"})
    assert res.status_code == 200, res.text
    exec_token = res.json()["token"]

    res = client.get(f"/api/sales/leads/{enquiry_id}", headers={"Authorization": f"Bearer {exec_token}"})
    assert res.status_code == 200, res.text
    ws = res.json()
    assert ws["enquiry_reference"] == ref_id
    assert ws["assigned_to"]["id"] == exec_id
    assert ws["ai_handoff_summary"] is not None
    print(f"✓ Step 8: Executive '{exec_name}' opened workspace with full AI Underwriting Briefing.")

    # Step 9: Executive updates status to CONTACTED
    res = client.patch(
        f"/api/sales/leads/{enquiry_id}/status",
        json={"new_status": "CONTACTED", "reason": "Called applicant via WhatsApp; verified TCS employment."},
        headers={"Authorization": f"Bearer {exec_token}"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["new_status"] == "CONTACTED"
    print("✓ Step 9: Lead status transitioned to CONTACTED.")

    # Step 10: Executive logs internal collaboration note
    res = client.post(
        f"/api/sales/leads/{enquiry_id}/notes",
        json={"note_content": "Aarav has 3 months salary slips ready. Wants to compare SBI repo benchmark against HDFC."},
        headers={"Authorization": f"Bearer {exec_token}"}
    )
    assert res.status_code == 200, res.text
    print("✓ Step 10: Internal collaboration note recorded.")

    # Step 11: Executive creates follow-up task
    due_tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    res = client.post(
        f"/api/sales/leads/{enquiry_id}/tasks",
        json={
            "task_type": "Document Collection",
            "description": "Collect TCS salary slips & Form 16",
            "due_at": due_tomorrow
        },
        headers={"Authorization": f"Bearer {exec_token}"}
    )
    assert res.status_code == 200, res.text
    task_id = res.json()["task_id"]
    print(f"✓ Step 11: Task '{task_id}' scheduled.")

    # Step 12: Executive completes task
    res = client.patch(f"/api/sales/tasks/{task_id}/complete", headers={"Authorization": f"Bearer {exec_token}"})
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "COMPLETED"
    print("✓ Step 12: Follow-up task marked COMPLETED.")

    # Step 13: Executive records bank application submission & updates sanction
    res = client.post(
        f"/api/sales/leads/{enquiry_id}/applications",
        json={
            "lender_name": "State Bank of India",
            "product_reference": "sbi-regular-home-loan",
            "application_reference": "SBI-HL-2026-90412",
            "initial_status": "SUBMITTED_TO_LENDER"
        },
        headers={"Authorization": f"Bearer {exec_token}"}
    )
    assert res.status_code == 200, res.text
    app_id = res.json()["application_id"]
    print(f"✓ Step 13: Bank application recorded (Ref: SBI-HL-2026-90412).")

    # Step 14: Lender approves application
    res = client.patch(
        f"/api/sales/applications/{app_id}/status",
        json={"status": "APPROVED"},
        headers={"Authorization": f"Bearer {exec_token}"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "APPROVED"

    # Step 15: Advance lead status to QUALIFIED
    res = client.patch(
        f"/api/sales/leads/{enquiry_id}/status",
        json={"new_status": "QUALIFIED", "reason": "SBI in-principle sanction approved for Rs 65 Lakhs."},
        headers={"Authorization": f"Bearer {exec_token}"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["new_status"] == "QUALIFIED"
    print("✓ Step 15: Lead successfully advanced to QUALIFIED stage!")

    print("\n=======================================================")
    print("🎉 ALL CREDENCE CRM E2E STEPS PASSED SUCCESSFULLY!")
    print("=======================================================\n")

if __name__ == "__main__":
    test_full_crm_lifecycle()

