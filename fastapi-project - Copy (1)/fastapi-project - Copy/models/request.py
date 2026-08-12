import enum
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from db.base import Base


class RequestStatus(str, enum.Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    FULFILLED = "Fulfilled"


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    food_type = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(
        Enum(RequestStatus),
        default=RequestStatus.PENDING,
        nullable=False,
        index=True,
    )
    notes = Column(Text, nullable=True)

    # ✅ تعديل: إضافة ondelete="CASCADE" لحذف الطلبات عند حذف الجمعية
    charity_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ✅ التعديل الأهم: إضافة ondelete="CASCADE" للسماح بحذف الوجبة (Donation) حتى لو لها طلبات
    donation_id = Column(Integer, ForeignKey("donations.id", ondelete="CASCADE"), nullable=False, index=True)

    date_requested = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    charity = relationship("User", back_populates="requests")
    donation = relationship("Donation", back_populates="requests")

    # Prevent duplicate requests from same charity for same donation
    __table_args__ = (
        UniqueConstraint("charity_id", "donation_id", name="uq_charity_donation_request"),
    )