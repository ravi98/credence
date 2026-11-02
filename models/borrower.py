from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from models.base import TimestampMixin

class BorrowerProfile(Base, TimestampMixin):
    __tablename__ = "borrower_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # Salaried, Self-Employed, etc.
    monthly_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    existing_monthly_obligations: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    self_reported_credit_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    preferred_loan_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="borrower_profile")

