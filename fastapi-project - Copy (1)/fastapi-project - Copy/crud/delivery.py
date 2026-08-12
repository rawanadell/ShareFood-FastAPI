from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.delivery import DeliveryAssignment, DeliveryStatus
from models.donation import Donation, DonationStatus
from models.user import User, UserRole
from schemas.delivery import AssignVolunteerRequest, DeliveryStatusUpdate


def assign_volunteer(
    db: Session, data: AssignVolunteerRequest, admin_id: int
) -> DeliveryAssignment:
    donation = db.query(Donation).filter(Donation.id == data.donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    if donation.status != DonationStatus.APPROVED:
        raise HTTPException(
            status_code=400, detail="Only approved donations can be assigned for delivery"
        )

    volunteer = db.query(User).filter(
        User.id == data.volunteer_id, User.role == UserRole.VOLUNTEER, User.is_active == True
    ).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    existing = db.query(DeliveryAssignment).filter(
        DeliveryAssignment.donation_id == data.donation_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="A volunteer is already assigned to this donation"
        )

    assignment = DeliveryAssignment(
        donation_id=data.donation_id,
        volunteer_id=data.volunteer_id,
        assigned_by=admin_id,
        notes=data.notes,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def get_assignment_by_donation(
    db: Session, donation_id: int
) -> Optional[DeliveryAssignment]:
    return db.query(DeliveryAssignment).filter(
        DeliveryAssignment.donation_id == donation_id
    ).first()


def get_volunteer_assignments(
    db: Session, volunteer_id: int
) -> list[DeliveryAssignment]:
    return (
        db.query(DeliveryAssignment)
        .filter(DeliveryAssignment.volunteer_id == volunteer_id)
        .order_by(DeliveryAssignment.assigned_at.desc())
        .all()
    )


def update_delivery_status(
    db: Session,
    assignment_id: int,
    data: DeliveryStatusUpdate,
    volunteer_id: int,
) -> DeliveryAssignment:
    assignment = db.query(DeliveryAssignment).filter(
        DeliveryAssignment.id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Delivery assignment not found")
    if assignment.volunteer_id != volunteer_id:
        raise HTTPException(
            status_code=403, detail="You are not assigned to this delivery"
        )

    assignment.status = data.status
    if data.notes:
        assignment.notes = data.notes
    if data.status == DeliveryStatus.DELIVERED:
        assignment.delivered_at = datetime.now(timezone.utc)
        # Cascade donation to Delivered
        donation = db.query(Donation).filter(
            Donation.id == assignment.donation_id
        ).first()
        if donation:
            donation.status = DonationStatus.DELIVERED

    db.commit()
    db.refresh(assignment)
    return assignment


def get_all_assignments(
    db: Session, skip: int = 0, limit: int = 20
) -> list[DeliveryAssignment]:
    return (
        db.query(DeliveryAssignment)
        .order_by(DeliveryAssignment.assigned_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
