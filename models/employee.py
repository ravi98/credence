from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from models.base import TimestampMixin

class EmployeeProfile(Base, TimestampMixin):
    __tablename__ = "employee_profiles"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(100), default="Loan Specialist", nullable=False)
    department: Mapped[str] = mapped_column(String(100), default="Sales & Advisory", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="employee_profile")
    memberships: Mapped[List["TeamMembership"]] = relationship("TeamMembership", back_populates="employee")

class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    manager_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    manager: Mapped[Optional["User"]] = relationship("User")
    members: Mapped[List["TeamMembership"]] = relationship("TeamMembership", back_populates="team", cascade="all, delete-orphan")
    enquiries: Mapped[List["LoanEnquiry"]] = relationship("LoanEnquiry", back_populates="assigned_team")

class TeamMembership(Base, TimestampMixin):
    __tablename__ = "team_memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("employee_profiles.user_id", ondelete="CASCADE"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    team: Mapped["Team"] = relationship("Team", back_populates="members")
    employee: Mapped["EmployeeProfile"] = relationship("EmployeeProfile", back_populates="memberships")
