from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func 
from db.session import get_db
from models.notification import Notification
from typing import Optional # 👈 استيراد لتأمين المتغير

router = APIRouter()

@router.get("")
@router.get("/")
def get_my_notifications(
    # 🔥 تعريف رسمي للمتغير عشان يظهر مربع الإدخال في السواجر
    user_id: Optional[int] = Query(None, description="رقم الـ ID بتاع الجمعية (مثال: 4)"), 
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Notification)
        
        # لو كتبتي رقم 4، هيجيب إشعارات الجمعية دي بس
        if user_id is not None:
            query = query.filter(Notification.user_id == user_id)
            
        # 🎲 الترتيب العشوائي للكوكتيل اللي هيظهر في الموبايل
        notifications = query.order_by(func.random()).limit(40).all()
        
        return [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "location": n.location or "القاهرة، مصر",
                "created_at": n.created_at.strftime("%Y-%m-%d %H:%M") if n.created_at else "الآن",
                "is_interactive": n.is_interactive,
                "security_code": n.security_code,
                "notification_type": "تحديث التبرع" if "DONATION" in str(n.notification_type) else "تحديث الطلب" if "REQUEST" in str(n.notification_type) else "تنبيه التوصيل"
            }
            for n in notifications
        ]
    except Exception as e:
        print(f"❌ Error in notifications route: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")