import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from db.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    DONOR = "Donor"
    CHARITY = "Charity"
    VOLUNTEER = "Volunteer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    phone_number = Column(String(20), nullable=True)
    role = Column(Enum(UserRole), nullable=False, index=True)

    # Location for nearby queries
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Volunteer-specific
    photo_url = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # --- Relationships ---
    
    donations = relationship("Donation", back_populates="donor", foreign_keys="Donation.donor_id")
    requests = relationship("Request", back_populates="charity")
    
    # علاقة التكليفات للمتطوع
    deliveries = relationship(
        "DeliveryAssignment", 
        back_populates="volunteer", 
        foreign_keys="DeliveryAssignment.volunteer_id"
    )
    
    # ✅ التعديل الجديد: ربط المستخدم بإشعاراته الخاصة
    # cascade="all, delete-orphan" عشان لو المستخدم اتمسح، إشعاراته تتمسح معاه تلقائياً
    notifications = relationship(
        "Notification", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    audit_logs = relationship("AuditLog", back_populates="actor")