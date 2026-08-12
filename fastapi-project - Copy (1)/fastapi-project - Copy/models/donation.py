import enum
from sqlalchemy import (
    Column, Integer, String, Text, Enum, DateTime,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from db.base import Base


class DonationStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    DELIVERED = "Delivered"
    REJECTED = "Rejected"


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    food_type = Column(String(100), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    expiry_time = Column(String, nullable=True)
    address = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    status = Column(
        Enum(DonationStatus),
        default=DonationStatus.PENDING,
        nullable=False,
        index=True,
    )
    rejection_reason = Column(Text, nullable=True)

    donor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    date_created = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # soft delete

    # Relationships
    donor = relationship("User", back_populates="donations", foreign_keys=[donor_id])
    approver = relationship("User", foreign_keys=[approved_by])
    requests = relationship("Request", back_populates="donation")
    
    # ✅ تعديل الاسم ليتوافق مع back_populates في ملف الـ delivery
    delivery_assignment = relationship("DeliveryAssignment", back_populates="donation", uselist=False)
    
    # ✅ رجعنا سطر الـ Notifications عشان السيستم يفضل شغال تمام
    notifications = relationship("Notification", back_populates="donation")
    
    status_history = relationship("AuditLog", back_populates="donation")

    __table_args__ = (
        Index("ix_donations_status_food_type", "status", "food_type"),
    )