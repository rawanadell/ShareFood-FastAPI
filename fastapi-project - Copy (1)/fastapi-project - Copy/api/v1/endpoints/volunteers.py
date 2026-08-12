from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.session import get_db
from core.dependencies import get_volunteer, get_admin
from crud.delivery import (
    assign_volunteer, get_volunteer_assignments,
    update_delivery_status, get_all_assignments, get_assignment_by_donation,
)
from models.user import User
from schemas.delivery import AssignVolunteerRequest, DeliveryStatusUpdate, DeliveryOut

router = APIRouter(prefix="/volunteers", tags=["Volunteers"])


@router.post("/assign", response_model=DeliveryOut)
def assign(
    data: AssignVolunteerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin),
):
    return assign_volunteer(db, data, current_user.id)


@router.get("/assigned-deliveries", response_model=list[DeliveryOut])
def my_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_volunteer),
):
    return get_volunteer_assignments(db, current_user.id)


@router.patch("/delivery-status/{assignment_id}", response_model=DeliveryOut)
def update_status(
    assignment_id: int,
    data: DeliveryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_volunteer),
):
    return update_delivery_status(db, assignment_id, data, current_user.id)


@router.post("/deliver/{assignment_id}", response_model=DeliveryOut)
def mark_delivered(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_volunteer),
):
    from models.delivery import DeliveryStatus
    data = DeliveryStatusUpdate(status=DeliveryStatus.DELIVERED)
    return update_delivery_status(db, assignment_id, data, current_user.id)


@router.get("/all", response_model=list[DeliveryOut])
def all_deliveries(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin),
):
    skip = (page - 1) * per_page
    return get_all_assignments(db, skip=skip, limit=per_page)
