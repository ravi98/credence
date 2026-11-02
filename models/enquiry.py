from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Any, Dict
from sqlalchemy import String, Numeric, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base, JSON_VARIANT
from models.base import TimestampMixin

class LeadStatus(str, Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    CONTACT_ATTEMPTED = "CONTACT_ATTEMPTED"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    NOT_QUALIFIED = "NOT_QUALIFIED"
    CLOSED_LOST = "CLOSED_LOST"

class ApplicationStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED_TO_LENDER = "SUBMITTED_TO_LENDER"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISBURSED = "DISBURSED"
    WITHDRAWN = "WITHDRAWN"

class SummaryStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class PreferenceType(str, Enum):
    PRIMARY = "PRIMARY"
    ALTERNATIVE = "ALTERNATIVE"

class LoanEnquiry(Base, TimestampMixin):
    __tablename__ = "loan_enquiries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enquiry_reference: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    customer_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    conversation_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    loan_category: Mapped[str] = mapped_column(String(50), nullable=False) # Home Loan, Personal Loan, etc.
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    preferred_tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)

    # 4-Part Submission Snapshots (Immutable point-in-time state)
    borrower_profile_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False)
    contact_details_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False)
    contact_preferences: Mapped[Dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False)

    # Assignment & Lifecycle
    assigned_team_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    current_lead_status: Mapped[LeadStatus] = mapped_column(
        SQLEnum(LeadStatus, name="lead_status_enum", native_enum=False),
        default=LeadStatus.NEW,
        nullable=False,
        index=True
    )

    # Asynchronous AI Handoff Summary
    ai_handoff_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON_VARIANT, nullable=True)
    summary_status: Mapped[SummaryStatus] = mapped_column(
        SQLEnum(SummaryStatus, name="summary_status_enum", native_enum=False),
        default=SummaryStatus.PENDING,
        nullable=False,
        index=True
    )
    summary_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    summary_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer: Mapped["User"] = relationship("User", foreign_keys=[customer_user_id], back_populates="enquiries")
    assigned_executive: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_user_id], back_populates="assigned_leads")
    assigned_team: Mapped[Optional["Team"]] = relationship("Team", back_populates="enquiries")

    products: Mapped[List["EnquiryProduct"]] = relationship(
        "EnquiryProduct", 
        back_populates="enquiry", 
        cascade="all, delete-orphan",
        order_by="EnquiryProduct.display_order"
    )
    applications: Mapped[List["LoanApplication"]] = relationship("LoanApplication", back_populates="enquiry", cascade="all, delete-orphan")
    assignments: Mapped[List["LeadAssignment"]] = relationship("LeadAssignment", back_populates="enquiry", cascade="all, delete-orphan")
    status_history: Mapped[List["LeadStatusHistory"]] = relationship("LeadStatusHistory", back_populates="enquiry", cascade="all, delete-orphan")
    notes: Mapped[List["LeadNote"]] = relationship("LeadNote", back_populates="enquiry", cascade="all, delete-orphan")
    tasks: Mapped[List["LeadTask"]] = relationship("LeadTask", back_populates="enquiry", cascade="all, delete-orphan")
    consents: Mapped[List["ConsentRecord"]] = relationship("ConsentRecord", back_populates="enquiry", cascade="all, delete-orphan")

class EnquiryProduct(Base, TimestampMixin):
    __tablename__ = "enquiry_products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enquiry_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_enquiries.id", ondelete="CASCADE"), nullable=False, index=True)
    product_reference: Mapped[str] = mapped_column(String(100), nullable=False) # scheme_slug or compact_key
    institution: Mapped[str] = mapped_column(String(100), nullable=False)
    scheme_name: Mapped[str] = mapped_column(String(150), nullable=False)
    preference_type: Mapped[PreferenceType] = mapped_column(
        SQLEnum(PreferenceType, name="preference_type_enum", native_enum=False),
        default=PreferenceType.PRIMARY,
        nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    product_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON_VARIANT, nullable=False) # Frozen rates, tenure cap, benchmarks

    enquiry: Mapped["LoanEnquiry"] = relationship("LoanEnquiry", back_populates="products")

class LoanApplication(Base, TimestampMixin):
    __tablename__ = "loan_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enquiry_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_enquiries.id", ondelete="CASCADE"), nullable=False, index=True)
    lender_name: Mapped[str] = mapped_column(String(100), nullable=False)
    product_reference: Mapped[str] = mapped_column(String(100), nullable=False)
    application_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # External bank reference
    current_status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus, name="application_status_enum", native_enum=False),
        default=ApplicationStatus.IN_PROGRESS,
        nullable=False,
        index=True
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    enquiry: Mapped["LoanEnquiry"] = relationship("LoanEnquiry", back_populates="applications")

class LeadAssignment(Base):
    __tablename__ = "lead_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enquiry_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_enquiries.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    team_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    unassigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assignment_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    enquiry: Mapped["LoanEnquiry"] = relationship("LoanEnquiry", back_populates="assignments")
    assigned_to: Mapped["User"] = relationship("User", foreign_keys=[assigned_to_user_id])
    assigned_by: Mapped["User"] = relationship("User", foreign_keys=[assigned_by_user_id])

class LeadStatusHistory(Base):
    __tablename__ = "lead_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enquiry_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_enquiries.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    enquiry: Mapped["LoanEnquiry"] = relationship("LoanEnquiry", back_populates="status_history")
    changed_by: Mapped["User"] = relationship("User")

class LeadNote(Base, TimestampMixin):
    __tablename__ = "lead_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enquiry_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_enquiries.id", ondelete="CASCADE"), nullable=False, index=True)
    author_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    note_content: Mapped[str] = mapped_column(Text, nullable=False)

    enquiry: Mapped["LoanEnquiry"] = relationship("LoanEnquiry", back_populates="notes")
    author: Mapped["User"] = relationship("User")

class LeadTask(Base, TimestampMixin):
    __tablename__ = "lead_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    enquiry_id: Mapped[str] = mapped_column(String(36), ForeignKey("loan_enquiries.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), default="Callback", nullable=False) # Callback, Document Follow-up, etc.
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False, index=True) # PENDING, COMPLETED, CANCELLED
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    enquiry: Mapped["LoanEnquiry"] = relationship("LoanEnquiry", back_populates="tasks")
    assigned_to: Mapped["User"] = relationship("User", foreign_keys=[assigned_to_user_id])

class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    enquiry_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("loan_enquiries.id", ondelete="SET NULL"), nullable=True, index=True)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False) # CREDENCE_CONTACT, LENDER_DATA_SHARING, MARKETING_COMMUNICATION
    consent_action: Mapped[str] = mapped_column(String(20), default="GRANTED", nullable=False)
    notice_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="ENQUIRY_FLOW", nullable=False)

    enquiry: Mapped[Optional["LoanEnquiry"]] = relationship("LoanEnquiry", back_populates="consents")
    user: Mapped["User"] = relationship("User")

