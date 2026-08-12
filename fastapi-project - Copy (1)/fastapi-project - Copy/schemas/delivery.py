from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

# ✅ تأكدي أن الاستيراد لا يسبب دائرة مغلقة (Circular Import)
# لو لسه فيه مشكلة، جربي استيراد Enum الحالة من ملف مستقل أو من models.delivery مباشرة
from models.delivery import DeliveryStatus


class AssignVolunteerRequest(BaseModel):
    donation_id: int
    volunteer_id: int
    notes: Optional[str] = None
    # ✅ إضافة الكود السري ليتم إنشاؤه عند التعيين
    security_code: Optional[str] = None 


class DeliveryStatusUpdate(BaseModel):
    status: DeliveryStatus
    notes: Optional[str] = None
    # ✅ إضافة الكود هنا تحسباً لأي تحديث
    security_code: Optional[str] = None


class DeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donation_id: int
    volunteer_id: int
    assigned_by: int
    status: DeliveryStatus
    notes: Optional[str]
    # ✅ أهم حقل عشان يظهر للمتطوع في الأبلكيشن
    security_code: Optional[str] = None 
    assigned_at: datetime
    delivered_at: Optional[datetime]
    updated_at: datetime