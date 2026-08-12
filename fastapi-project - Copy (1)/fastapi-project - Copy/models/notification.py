import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.base import Base 

# 1️⃣ إضافة Enum لتحديد نوع الإشعار (للفصل المنطقي)
class NotificationType(str, enum.Enum):
    DONATION_UPDATE = "DonationUpdate"   # خاصة بالفنادق (مثلاً: تم قبول تبرعك)
    REQUEST_UPDATE = "RequestUpdate"     # خاصة بالجمعيات (مثلاً: تم قبول طلبك)
    DELIVERY_ALERT = "DeliveryAlert"     # خاصة بالمتطوعين أو أكواد التسليم

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # صاحب الإشعار (مهم جداً للفصل: كل user يشوف حاجته بس)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # التبرع المرتبط به
    donation_id = Column(Integer, ForeignKey("donations.id", ondelete="CASCADE"), nullable=True, index=True)
    
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    location = Column(String(255), nullable=True)
    
    # 2️⃣ تحديد النوع عشان الـ Flutter يغير الأيقونة أو اللون حسب المستخدم
    notification_type = Column(Enum(NotificationType), default=NotificationType.DONATION_UPDATE)
    
    is_interactive = Column(Boolean, default=False)
    security_code = Column(String(10), nullable=True)
    
    # 3️⃣ إضافة حالة "تمت القراءة" (ضرورية جداً في الـ UI)
    is_read = Column(Boolean, default=False)
    
    # توحيد صيغة الوقت مع موديل الـ Request اللي بعتيه قبل كدة
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )

    # 🔄 العلاقات العكسية
    donation = relationship("Donation", back_populates="notifications")
    user = relationship("User", back_populates="notifications")