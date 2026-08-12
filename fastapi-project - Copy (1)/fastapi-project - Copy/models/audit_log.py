from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(Integer, ForeignKey("donations.id"), nullable=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    action = Column(String(100), nullable=False)       # e.g. "APPROVED", "REJECTED", "STATUS_CHANGED"
    old_value = Column(String(100), nullable=True)
    new_value = Column(String(100), nullable=True)
    detail = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    donation = relationship("Donation", back_populates="status_history")
    actor = relationship("User", back_populates="audit_logs")
