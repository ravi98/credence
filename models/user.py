from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from models.base import TimestampMixin

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    SALES_EXECUTIVE = "SALES_EXECUTIVE"
    SALES_MANAGER = "SALES_MANAGER"
    SALES_ADMIN = "SALES_ADMIN"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.CUSTOMER,
        nullable=False,
        index=True
    )
    auth_provider: Mapped[str] = mapped_column(String(50), default="email", nullable=False)
    google_id: Mapped[Optional[str]] = mapped_column(String(100), unique=False, index=True, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    employee_profile: Mapped[Optional["EmployeeProfile"]] = relationship(
        "EmployeeProfile", 
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    borrower_profile: Mapped[Optional["BorrowerProfile"]] = relationship(
        "BorrowerProfile", 
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    enquiries: Mapped[List["LoanEnquiry"]] = relationship(
        "LoanEnquiry", 
        back_populates="customer",
        foreign_keys="LoanEnquiry.customer_user_id"
    )
    assigned_leads: Mapped[List["LoanEnquiry"]] = relationship(
        "LoanEnquiry", 
        back_populates="assigned_executive",
        foreign_keys="LoanEnquiry.assigned_to_user_id"
    )

