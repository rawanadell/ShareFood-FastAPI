from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models.request import Request, RequestStatus
from models.donation import Donation, DonationStatus
from schemas.request import RequestCreate


def create_request(db: Session, data: RequestCreate, charity_id: int) -> Request:
    # 1. التأكد من وجود الوجبة
    donation = db.query(Donation).filter(Donation.id == data.donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")

    # 2. التأكد من الحالة (Security Checks)
    if donation.status in (DonationStatus.DELIVERED, DonationStatus.REJECTED):
        raise HTTPException(status_code=400, detail="الوجبة محجوزة بالفعل أو مرفوضة")
    
    if donation.status == DonationStatus.PENDING:
        raise HTTPException(status_code=400, detail="الوجبة لم يتم الموافقة عليها بعد")

    # 3. إنشاء الطلب
    req = Request(
        donation_id=data.donation_id,
        charity_id=charity_id,
        food_type=data.food_type,
        quantity=data.quantity,
        notes=data.notes,
    )
    
    try:
        db.add(req)
        # 🔔 تحديث حالة الوجبة (SQLAlchemy هيعرف لوحده إنها اتعدلت)
        donation.status = DonationStatus.DELIVERED 
        
        db.commit() # الحفظ النهائي للكل
        db.refresh(req) # تحديث البيانات للقراءة فقط
        return req
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="لقد قمت بطلب هذه الوجبة مسبقاً")
    except Exception as e:
        db.rollback()
        print(f"❌ Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail="خطأ داخلي في السيرفر")


def get_request(db: Session, request_id: int) -> Optional[Request]:
    return db.query(Request).filter(Request.id == request_id).first()


def get_requests(
    db: Session,
    charity_id: Optional[int] = None,
    donation_id: Optional[int] = None,
    req_status: Optional[RequestStatus] = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Request], int]:
    q = db.query(Request)
    if charity_id:
        q = q.filter(Request.charity_id == charity_id)
    if donation_id:
        q = q.filter(Request.donation_id == donation_id)
    if req_status:
        q = q.filter(Request.status == req_status)
    total = q.count()
    items = q.order_by(Request.date_requested.desc()).offset(skip).limit(limit).all()
    return items, total


def update_request_status(
    db: Session, req: Request, new_status: RequestStatus
) -> Request:
    req.status = new_status
    if new_status == RequestStatus.FULFILLED:
        # Mark donation delivered when request fulfilled
        from models.donation import Donation, DonationStatus
        donation = db.query(Donation).filter(Donation.id == req.donation_id).first()
        if donation and donation.status == DonationStatus.APPROVED:
            donation.status = DonationStatus.DELIVERED
    db.commit()
    db.refresh(req)
    return req
