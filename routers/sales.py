import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, String, cast

from database import get_db
from auth_deps import get_current_user, require_roles, get_authorized_lead
from models.user import User, UserRole
from models.employee import EmployeeProfile, Team, TeamMembership
from models.enquiry import (
    LoanEnquiry,
    EnquiryProduct,
    LoanApplication,
    LeadAssignment,
    LeadStatusHistory,
    LeadNote,
    LeadTask,
    LeadStatus,
    ApplicationStatus,
    PreferenceType
)

router = APIRouter()

SALES_ROLES = [
    UserRole.SALES_EXECUTIVE,
    UserRole.SALES_MANAGER,
    UserRole.SALES_ADMIN,
    UserRole.SYSTEM_ADMIN
]

MANAGEMENT_ROLES = [
    UserRole.SALES_MANAGER,
    UserRole.SALES_ADMIN,
    UserRole.SYSTEM_ADMIN
]

# ==================== Pydantic Schemas ====================

class UpdateLeadStatusRequest(BaseModel):
    new_status: str
    reason: Optional[str] = None

class CreateNoteRequest(BaseModel):
    note_content: str = Field(..., min_length=1, max_length=5000)

class CreateTaskRequest(BaseModel):
    task_type: str = "Callback" # Callback, Document Collection, Bank Follow-up, Verification
    description: str = Field(..., min_length=2, max_length=1000)
    due_at: datetime
    assigned_to_user_id: Optional[str] = None

class AssignLeadRequest(BaseModel):
    assigned_to_user_id: str
    team_id: Optional[str] = None
    assignment_reason: Optional[str] = None

class CreateApplicationRequest(BaseModel):
    lender_name: str
    product_reference: str
    application_reference: Optional[str] = None
    initial_status: str = "IN_PROGRESS"

class UpdateApplicationStatusRequest(BaseModel):
    status: str

# ==================== Helper: Scoped Lead Query ====================

def get_scoped_lead_query(current_user: User, db: Session):
    user_role = current_user.role
    if isinstance(user_role, str):
        try:
            user_role = UserRole(user_role)
        except ValueError:
            pass

    query = db.query(LoanEnquiry)

    if user_role in (UserRole.SALES_ADMIN, UserRole.SYSTEM_ADMIN):
        return query

    if user_role == UserRole.SALES_MANAGER:
        manager_team_ids = []
        if current_user.employee_profile and current_user.employee_profile.memberships:
            manager_team_ids = [m.team_id for m in current_user.employee_profile.memberships]
        
        teams_managed = db.query(Team.id).filter(Team.manager_user_id == current_user.id).all()
        for t in teams_managed:
            if t[0] not in manager_team_ids:
                manager_team_ids.append(t[0])

        if manager_team_ids:
            team_exec_user_ids = db.query(TeamMembership.employee_user_id).filter(
                TeamMembership.team_id.in_(manager_team_ids)
            ).all()
            team_user_ids = [uid[0] for uid in team_exec_user_ids]
            team_user_ids.append(current_user.id)

            return query.filter(
                or_(
                    LoanEnquiry.assigned_team_id.in_(manager_team_ids),
                    LoanEnquiry.assigned_to_user_id.in_(team_user_ids),
                    LoanEnquiry.assigned_to_user_id.is_(None)
                )
            )

        # When no restrictive team partition is configured, a Sales Manager oversees all sales leads across the department
        return query

    # SALES_EXECUTIVE: Strict ownership
    return query.filter(LoanEnquiry.assigned_to_user_id == current_user.id)

# ==================== Endpoints ====================

@router.get("/dashboard")
async def get_sales_dashboard(
    current_user: User = Depends(require_roles(*SALES_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Returns metrics, status breakdowns, and urgent tasks tailored to user's authorized scope.
    """
    scoped_query = get_scoped_lead_query(current_user, db)

    total_leads = scoped_query.count()

    # Status counts
    status_counts = {}
    for st in LeadStatus:
        count = scoped_query.filter(LoanEnquiry.current_lead_status == st).count()
        status_counts[st.value] = count

    # Pipeline volume sum
    total_pipeline_val = db.query(func.coalesce(func.sum(LoanEnquiry.requested_amount), 0)).filter(
        LoanEnquiry.id.in_(scoped_query.with_entities(LoanEnquiry.id))
    ).scalar()

    # Overdue and upcoming tasks
    now_utc = datetime.now(timezone.utc)
    tasks_query = db.query(LeadTask).filter(
        LeadTask.status == "PENDING"
    )
    if current_user.role == UserRole.SALES_EXECUTIVE:
        tasks_query = tasks_query.filter(LeadTask.assigned_to_user_id == current_user.id)

    pending_tasks_count = tasks_query.count()
    overdue_tasks_count = tasks_query.filter(LeadTask.due_at < now_utc).count()

    # Conversion metric: QUALIFIED / (total_leads or 1)
    qualified_count = status_counts.get("QUALIFIED", 0)
    conversion_rate = round((qualified_count / total_leads * 100), 1) if total_leads > 0 else 0.0

    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        },
        "metrics": {
            "total_leads": total_leads,
            "pipeline_volume": float(total_pipeline_val),
            "conversion_rate_pct": conversion_rate,
            "pending_tasks": pending_tasks_count,
            "overdue_tasks": overdue_tasks_count
        },
        "status_breakdown": status_counts
    }

@router.get("/leads")
async def list_sales_leads(
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_roles(*SALES_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Returns scoped leads inbox with filtering, search, and pagination.
    """
    query = get_scoped_lead_query(current_user, db)

    if status and status != "ALL":
        query = query.filter(LoanEnquiry.current_lead_status == status)

    if category and category != "ALL":
        query = query.filter(LoanEnquiry.loan_category == category)

    if search:
        s = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(LoanEnquiry.enquiry_reference).like(s),
                func.lower(cast(LoanEnquiry.contact_details_snapshot, String)).like(s)
            )
        )

    total_matched = query.count()
    leads = query.order_by(desc(LoanEnquiry.created_at)).offset(offset).limit(limit).all()

    items = []
    for enq in leads:
        primary_p = None
        for p in enq.products:
            if getattr(p, "preference_type", None) == PreferenceType.PRIMARY or str(p.preference_type).endswith("PRIMARY"):
                primary_p = p
                break
        if not primary_p and enq.products:
            primary_p = enq.products[0]

        borrower_info = enq.borrower_profile_snapshot or {}

        items.append({
            "id": enq.id,
            "enquiry_reference": enq.enquiry_reference,
            "customer_name": borrower_info.get("full_name") or "Applicant",
            "customer_phone": borrower_info.get("phone") or "",
            "customer_city": borrower_info.get("city") or "",
            "loan_category": enq.loan_category,
            "requested_amount": float(enq.requested_amount) if enq.requested_amount else 0,
            "preferred_tenure_months": enq.preferred_tenure_months,
            "current_status": enq.current_lead_status.value if hasattr(enq.current_lead_status, "value") else str(enq.current_lead_status),
            "summary_status": enq.summary_status.value if hasattr(enq.summary_status, "value") else str(enq.summary_status),
            "assigned_to": {
                "id": enq.assigned_executive.id,
                "name": enq.assigned_executive.name
            } if enq.assigned_executive else None,
            "primary_product": {
                "institution": primary_p.institution if primary_p else "Partner Bank",
                "scheme_name": primary_p.scheme_name if primary_p else "Loan Scheme",
                "interest_rate": primary_p.product_snapshot.get("interest_rate_range") if primary_p and primary_p.product_snapshot else "Market Rate"
            } if primary_p else None,
            "created_at": enq.created_at.isoformat() if enq.created_at else None
        })

    return {
        "total": total_matched,
        "limit": limit,
        "offset": offset,
        "leads": items
    }

@router.get("/leads/{lead_id}")
async def get_lead_workspace(
    lead_id: str,
    current_user: User = Depends(require_roles(*SALES_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Returns complete sales workspace for a lead, including frozen AI underwriting briefing,
    products, internal notes, follow-up tasks, and bank application records.
    """
    lead = get_authorized_lead(lead_id, current_user, db)

    # Products
    products_data = []
    for p in lead.products:
        pref = p.preference_type.value if hasattr(p.preference_type, "value") else str(p.preference_type)
        products_data.append({
            "id": p.id,
            "product_reference": p.product_reference,
            "institution": p.institution,
            "scheme_name": p.scheme_name,
            "preference_type": pref,
            "product_snapshot": p.product_snapshot
        })

    # Notes
    notes_data = []
    for n in (lead.notes or []):
        notes_data.append({
            "id": n.id,
            "note_content": n.note_content,
            "author_name": n.author.name if n.author else "Officer",
            "created_at": n.created_at.isoformat() if n.created_at else None
        })

    # Tasks
    tasks_data = []
    for t in (lead.tasks or []):
        tasks_data.append({
            "id": t.id,
            "task_type": t.task_type,
            "description": t.description,
            "due_at": t.due_at.isoformat() if t.due_at else None,
            "status": t.status,
            "assigned_to_name": t.assigned_to.name if t.assigned_to else "Assigned Officer",
            "completed_at": t.completed_at.isoformat() if t.completed_at else None
        })

    # Applications
    applications_data = []
    for a in (lead.applications or []):
        curr_st = a.current_status.value if hasattr(a.current_status, "value") else str(a.current_status)
        applications_data.append({
            "id": a.id,
            "lender_name": a.lender_name,
            "product_reference": a.product_reference,
            "application_reference": a.application_reference,
            "current_status": curr_st,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None
        })

    # Status History
    history_data = []
    for h in (lead.status_history or []):
        history_data.append({
            "id": h.id,
            "previous_status": h.previous_status,
            "new_status": h.new_status,
            "reason": h.reason,
            "changed_by": h.changed_by.name if h.changed_by else "System",
            "created_at": h.created_at.isoformat() if h.created_at else None
        })

    return {
        "id": lead.id,
        "enquiry_reference": lead.enquiry_reference,
        "customer_user_id": lead.customer_user_id,
        "loan_category": lead.loan_category,
        "requested_amount": float(lead.requested_amount) if lead.requested_amount else 0,
        "preferred_tenure_months": lead.preferred_tenure_months,
        "current_status": lead.current_lead_status.value if hasattr(lead.current_lead_status, "value") else str(lead.current_lead_status),
        "assigned_to": {
            "id": lead.assigned_executive.id,
            "name": lead.assigned_executive.name,
            "email": lead.assigned_executive.email
        } if lead.assigned_executive else None,
        "assigned_team": {
            "id": lead.assigned_team.id,
            "name": lead.assigned_team.name
        } if lead.assigned_team else None,
        "borrower_profile_snapshot": lead.borrower_profile_snapshot,
        "contact_details_snapshot": lead.contact_details_snapshot,
        "contact_preferences": lead.contact_preferences,
        "ai_handoff_summary": lead.ai_handoff_summary,
        "summary_status": lead.summary_status.value if hasattr(lead.summary_status, "value") else str(lead.summary_status),
        "summary_generated_at": lead.summary_generated_at.isoformat() if lead.summary_generated_at else None,
        "products": products_data,
        "notes": notes_data,
        "tasks": tasks_data,
        "applications": applications_data,
        "status_history": history_data,
        "created_at": lead.created_at.isoformat() if lead.created_at else None
    }

@router.patch("/leads/{lead_id}/status")
async def update_lead_status(
    lead_id: str,
    req: UpdateLeadStatusRequest,
    current_user: User = Depends(require_roles(*SALES_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Transitions the lifecycle status of a lead and records an audit log entry.
    """
    lead = get_authorized_lead(lead_id, current_user, db)

    try:
        new_status_enum = LeadStatus(req.new_status.strip().upper())
    except ValueError:
        valid_options = [s.value for s in LeadStatus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{req.new_status}'. Allowed: {', '.join(valid_options)}"
        )

    prev_status = lead.current_lead_status.value if hasattr(lead.current_lead_status, "value") else str(lead.current_lead_status)
    lead.current_lead_status = new_status_enum

    # If closing
    if new_status_enum in (LeadStatus.QUALIFIED, LeadStatus.CLOSED_LOST, LeadStatus.NOT_QUALIFIED):
        lead.closed_at = datetime.now(timezone.utc)

    # Log history
    history = LeadStatusHistory(
        id=f"lsh_{uuid.uuid4().hex[:12]}",
        enquiry_id=lead.id,
        previous_status=prev_status,
        new_status=new_status_enum.value,
        changed_by_user_id=current_user.id,
        reason=req.reason or f"Status updated by {current_user.name}"
    )
    db.add(history)
    db.commit()
    db.refresh(lead)

    return {
        "success": True,
        "lead_id": lead.id,
        "previous_status": prev_status,
        "new_status": new_status_enum.value
    }

@router.post("/leads/{lead_id}/notes")
async def add_lead_note(
    lead_id: str,
    req: CreateNoteRequest,
    current_user: User = Depends(require_roles(*SALES_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Appends an internal note to the lead's collaboration timeline.
    """
    lead = get_authorized_lead(lead_id, current_user, db)

    note = LeadNote(
        id=f"nt_{uuid.uuid4().hex[:12]}",
        enquiry_id=lead.id,
        author_user_id=current_user.id,
        note_content=req.note_content.strip()
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        "success": True,
        "note_id": note.id,
        "note_content": note.note_content,
        "author_name": current_user.name,
        "created_at": note.created_at.isoformat() if note.created_at else datetime.now(timezone.utc).isoformat()
    }

@router.post("/leads/{lead_id}/tasks")
async def add_lead_task(
    lead_id: str,
    req: CreateTaskRequest,
    current_user: User = Depends(require_roles(*SALES_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Schedules a follow-up task (Callback, Doc Collection, Verification) with deadline.
    """
    lead = get_authorized_lead(lead_id, current_user, db)

    assignee_id = req.assigned_to_user_id or current_user.id

    task = LeadTask(
        id=f"tsk_{uuid.uuid4().hex[:12]}",
        enquiry_id=lead.id,
        assigned_to_user_id=assignee_id,
        created_by_user_id=current_user.id,
        task_type=req.task_type,
        description=req.description.strip(),
        due_at=req.due_at,
        status="PENDING"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return {
        "success": True,
        "task_id": task.id,
        "task_type": task.task_type,
        "description": task.description,
        "due_at": task.due_at.isoformat(),
        "status": task.status
    }

@router.patch("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    current_user: User = Depends(require_roles(*SALES_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Marks a follow-up task as COMPLETED.
    """
    task = db.query(LeadTask).filter(LeadTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    task.status = "COMPLETED"
    task.completed_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "success": True,
        "task_id": task.id,
        "status": "COMPLETED"
    }

@router.post("/leads/{lead_id}/assign")
async def assign_lead(
    lead_id: str,
    req: AssignLeadRequest,
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Assigns or transfers a lead to a sales executive or team. Restricted to Managers and Admins.
    """
    lead = db.query(LoanEnquiry).filter(LoanEnquiry.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    target_officer = db.query(User).filter(User.id == req.assigned_to_user_id).first()
    if not target_officer:
        raise HTTPException(status_code=404, detail="Assigned user not found.")

    lead.assigned_to_user_id = target_officer.id
    if req.team_id:
        lead.assigned_team_id = req.team_id

    # If lead was NEW, transition to ASSIGNED
    prev_status = lead.current_lead_status.value if hasattr(lead.current_lead_status, "value") else str(lead.current_lead_status)
    if lead.current_lead_status == LeadStatus.NEW:
        lead.current_lead_status = LeadStatus.ASSIGNED

    # Record assignment log
    assignment_log = LeadAssignment(
        id=f"asg_{uuid.uuid4().hex[:12]}",
        enquiry_id=lead.id,
        assigned_to_user_id=target_officer.id,
        assigned_by_user_id=current_user.id,
        team_id=req.team_id,
        assignment_reason=req.assignment_reason or "Manual manager assignment"
    )
    db.add(assignment_log)

    # Record status history
    status_entry = LeadStatusHistory(
        id=f"lsh_{uuid.uuid4().hex[:12]}",
        enquiry_id=lead.id,
        previous_status=prev_status,
        new_status=lead.current_lead_status.value if hasattr(lead.current_lead_status, "value") else str(lead.current_lead_status),
        changed_by_user_id=current_user.id,
        reason=f"Assigned to {target_officer.name} by {current_user.name}"
    )
    db.add(status_entry)

    db.commit()

    return {
        "success": True,
        "lead_id": lead.id,
        "assigned_to": {
            "id": target_officer.id,
            "name": target_officer.name
        },
        "current_status": lead.current_lead_status.value if hasattr(lead.current_lead_status, "value") else str(lead.current_lead_status)
    }

@router.post("/leads/{lead_id}/applications")
async def add_loan_application(
    lead_id: str,
    req: CreateApplicationRequest,
    current_user: User = Depends(require_roles(*SALES_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Logs an official bank/NBFC application submission and external reference.
    """
    lead = get_authorized_lead(lead_id, current_user, db)

    try:
        app_status = ApplicationStatus(req.initial_status.upper())
    except ValueError:
        app_status = ApplicationStatus.IN_PROGRESS

    app = LoanApplication(
        id=f"app_{uuid.uuid4().hex[:12]}",
        enquiry_id=lead.id,
        lender_name=req.lender_name.strip(),
        product_reference=req.product_reference.strip(),
        application_reference=req.application_reference.strip() if req.application_reference else None,
        current_status=app_status,
        submitted_at=datetime.now(timezone.utc)
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    return {
        "success": True,
        "application_id": app.id,
        "lender_name": app.lender_name,
        "application_reference": app.application_reference,
        "status": app.current_status.value if hasattr(app.current_status, "value") else str(app.current_status)
    }

@router.patch("/applications/{app_id}/status")
async def update_application_status(
    app_id: str,
    req: UpdateApplicationStatusRequest,
    current_user: User = Depends(require_roles(*SALES_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Updates the lender sanction/disbursal status of a bank application.
    """
    app = db.query(LoanApplication).filter(LoanApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application record not found.")

    try:
        new_status = ApplicationStatus(req.status.strip().upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid application status '{req.status}'")

    app.current_status = new_status
    db.commit()

    return {
        "success": True,
        "application_id": app.id,
        "status": new_status.value
    }

@router.get("/team")
async def get_sales_team(
    current_user: User = Depends(require_roles(*MANAGEMENT_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Returns list of sales executives and team workload for lead distribution.
    """
    executives = db.query(User).filter(
        User.role.in_([UserRole.SALES_EXECUTIVE, UserRole.SALES_MANAGER])
    ).all()

    team_data = []
    for u in executives:
        assigned_count = db.query(LoanEnquiry).filter(LoanEnquiry.assigned_to_user_id == u.id).count()
        active_count = db.query(LoanEnquiry).filter(
            LoanEnquiry.assigned_to_user_id == u.id,
            LoanEnquiry.current_lead_status.notin_([LeadStatus.QUALIFIED, LeadStatus.CLOSED_LOST, LeadStatus.NOT_QUALIFIED])
        ).count()

        team_data.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role.value if hasattr(u.role, "value") else str(u.role),
            "total_assigned_leads": assigned_count,
            "active_leads": active_count
        })

    return {
        "team_members": team_data
    }

