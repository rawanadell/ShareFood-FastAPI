from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.donation import Donation, DonationStatus
from models.audit_log import AuditLog
from schemas.donation import DonationCreate, DonationUpdate


def _log(
    db: Session,
    donation_id: int,
    actor_id: int,
    action: str,
    old_val: str = None,
    new_val: str = None,
    detail: str = None,
):
    log = AuditLog(
        donation_id=donation_id,
        actor_id=actor_id,
        action=action,
        old_value=old_val,
        new_value=new_val,
        detail=detail,
    )
    db.add(log)


def create_donation(db: Session, obj_in: DonationCreate, donor_id: int):
    db_obj = Donation(
        title=obj_in.title,
        description=obj_in.description,
        food_type=obj_in.food_type,
        quantity=obj_in.quantity,
        address=obj_in.address,
        
        # 🔔 السطر السحري: بياخد الصلاحية اللي الفندق كتبها ويحفظها في قاعدة البيانات
        expiry_time=obj_in.expiry_time, 
        
        donor_id=donor_id,
        status=DonationStatus.APPROVED # الوجبة بتنزل قيد المراجعة في الأول
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_donation(db: Session, donation_id: int) -> Optional[Donation]:
    return (
        db.query(Donation)
        .filter(Donation.id == donation_id, Donation.deleted_at.is_(None))
        .first()
    )


def get_donations(
    db: Session,
    status: Optional[DonationStatus] = None,
    food_type: Optional[str] = None,
    donor_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Donation], int]:
    q = db.query(Donation).filter(Donation.deleted_at.is_(None))
    if status:
        q = q.filter(Donation.status == status)
    if food_type:
        q = q.filter(Donation.food_type.ilike(f"%{food_type}%"))
    if donor_id:
        q = q.filter(Donation.donor_id == donor_id)
    if search:
        q = q.filter(Donation.title.ilike(f"%{search}%"))
    total = q.count()
    items = q.order_by(Donation.date_created.desc()).offset(skip).limit(limit).all()
    return items, total


def get_available_donations(db: Session, skip: int = 0, limit: int = 100):
    # 🔍 اتأكدي إن الفلتر فيه DonationStatus.APPROVED فقط
    query = db.query(Donation).filter(
        Donation.status == DonationStatus.APPROVED, 
        Donation.deleted_at == None
    )
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def update_donation(
    db: Session, donation: Donation, data: DonationUpdate, actor_id: int
) -> Donation:
    if donation.status != DonationStatus.PENDING:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending donations can be edited",
        )
    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(donation, field, value)
    _log(db, donation.id, actor_id, "UPDATED", detail=str(update_fields))
    db.commit()
    db.refresh(donation)
    return donation


def soft_delete_donation(db: Session, donation: Donation, actor_id: int) -> Donation:
    if donation.status == DonationStatus.APPROVED:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approved donations cannot be deleted",
        )
    donation.deleted_at = datetime.now(timezone.utc)
    _log(db, donation.id, actor_id, "DELETED")
    db.commit()
    return donation


def approve_donation(db: Session, donation: Donation, admin_id: int) -> Donation:
    if donation.status != DonationStatus.PENDING:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending donations can be approved",
        )
    old = donation.status.value
    donation.status = DonationStatus.APPROVED
    donation.approved_by = admin_id
    _log(db, donation.id, admin_id, "APPROVED", old_val=old, new_val=DonationStatus.APPROVED.value)
    db.commit()
    db.refresh(donation)
    return donation


def reject_donation(
    db: Session, donation: Donation, admin_id: int, reason: str
) -> Donation:
    if donation.status not in (DonationStatus.PENDING, DonationStatus.APPROVED):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Donation cannot be rejected in its current state",
        )
    old = donation.status.value
    donation.status = DonationStatus.REJECTED
    donation.rejection_reason = reason
    _log(
        db, donation.id, admin_id, "REJECTED",
        old_val=old, new_val=DonationStatus.REJECTED.value, detail=reason,
    )
    db.commit()
    db.refresh(donation)
    return donation


def mark_delivered(db: Session, donation: Donation, actor_id: int) -> Donation:
    if donation.status != DonationStatus.APPROVED:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only approved donations can be marked delivered",
        )
    old = donation.status.value
    donation.status = DonationStatus.DELIVERED
    _log(
        db, donation.id, actor_id, "DELIVERED",
        old_val=old, new_val=DonationStatus.DELIVERED.value,
    )
    db.commit()
    db.refresh(donation)
    return donation


def get_audit_trail(db: Session, donation_id: int) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.donation_id == donation_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )
