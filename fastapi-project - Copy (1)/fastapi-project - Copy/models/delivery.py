from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

# استيراد الـ Base من المسار اللي اتأكدنا إنه شغال عندك
from db.base import Base 

class DeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class DeliveryAssignment(Base):
    __tablename__ = "delivery_assignments"

    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(Integer, ForeignKey("donations.id", ondelete="CASCADE"))
    volunteer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    assigned_by = Column(Integer, ForeignKey("users.id"))
    
    status = Column(String, default=DeliveryStatus.PENDING)
    notes = Column(String, nullable=True)

    # حقل الـ OTP (الـ security_code)
    security_code = Column(String, nullable=True) 
    
    assigned_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ إضافة العلاقات اللي الـ Mapper بيدور عليها
    # تأكدي أن "Donation" جواه علاقة اسمها "delivery_assignment"
    donation = relationship("Donation", back_populates="delivery_assignment")
    
    # تأكدي أن الـ User جواه علاقة اسمها "delivery_assignments"
    volunteer = relationship("User", foreign_keys=[volunteer_id])