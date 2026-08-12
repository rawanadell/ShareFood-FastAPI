from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.user import User, UserRole
from models.donation import Donation, DonationStatus
from models.request import Request, RequestStatus
# تأكدي من استيراد موديل الـ Delivery لو موجود عندك
# from models.delivery import Delivery 

class AdminReport(BaseModel):
    total_users: int
    total_donors: int
    total_charities: int
    total_volunteers: int
    total_admins: int
    total_donations: int
    pending_donations: int
    approved_donations: int
    delivered_donations: int
    rejected_donations: int
    total_requests: int
    pending_requests: int
    fulfilled_requests: int
    total_deliveries: int
    completed_deliveries: int

    class Config:
        from_attributes = True

# ✅ الدالة اللي كانت ناقصة ومسببة الإيرور
def generate_report(db: Session) -> AdminReport:
    return AdminReport(
        total_users=db.query(User).count(),
        total_donors=db.query(User).filter(User.role == UserRole.DONOR).count(),
        total_charities=db.query(User).filter(User.role == UserRole.CHARITY).count(),
        total_volunteers=db.query(User).filter(User.role == UserRole.VOLUNTEER).count(),
        total_admins=db.query(User).filter(User.role == UserRole.ADMIN).count(),
        
        total_donations=db.query(Donation).count(),
        pending_donations=db.query(Donation).filter(Donation.status == DonationStatus.PENDING).count(),
        approved_donations=db.query(Donation).filter(Donation.status == DonationStatus.APPROVED).count(),
        delivered_donations=db.query(Donation).filter(Donation.status == DonationStatus.DELIVERED).count(),
        rejected_donations=db.query(Donation).filter(Donation.status == DonationStatus.REJECTED).count(),
        
        total_requests=db.query(Request).count(),
        pending_requests=db.query(Request).filter(Request.status == RequestStatus.PENDING).count(),
        fulfilled_requests=db.query(Request).filter(Request.status == RequestStatus.FULFILLED).count(),
        
        total_deliveries=0, # db.query(Delivery).count() لو الموديل موجود
        completed_deliveries=0 # db.query(Delivery).filter(Delivery.status == "completed").count()
    )