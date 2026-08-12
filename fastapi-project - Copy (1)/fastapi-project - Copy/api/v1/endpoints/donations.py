from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form, Request
from sqlalchemy.orm import Session
import os

from db.session import get_db
from core.dependencies import get_current_user, get_donor, get_admin
from crud.donation import (
    create_donation, get_donation, get_donations, get_available_donations,
    update_donation, soft_delete_donation, approve_donation, reject_donation,
    mark_delivered, get_audit_trail,
)
from models.user import User, UserRole
from models.donation import DonationStatus
from schemas.donation import (
    DonationCreate, DonationUpdate, DonationOut, 
    PaginatedDonations, RejectRequest, StatusUpdateRequest,
)
from models.request import Request as DonationRequest, RequestStatus

router = APIRouter(prefix="/donations", tags=["Donations"])

def _get_or_404(db, donation_id):
    d = get_donation(db, donation_id)
    if not d:
        raise HTTPException(status_code=404, detail="Donation not found")
    return d

# ── 1. Create with Image ──────────────────────────────────────────────────────

@router.post("/with-image", status_code=status.HTTP_201_CREATED)
async def add_donation_with_image(
    title: str = Form(...),
    quantity: int = Form(...),
    description: str = Form(None),
    address: str = Form(None),
    food_type: str = Form(...),
    expiry_time: str = Form("6 ساعات"),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_donor),
):
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    file_path = os.path.join(upload_dir, image.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await image.read())
        
    data = DonationCreate(
        title=title, 
        quantity=quantity, 
        description=description,
        address=address, 
        food_type=food_type, 
        expiry_time=expiry_time,
        photo_url = f"/uploads/{image.filename}" 
    )
    return create_donation(db, data, current_user.id)

# ── 2. Browse / Search ────────────────────────────────────────────────────────

@router.get("/available", response_model=PaginatedDonations)
def available_donations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    skip = (page - 1) * per_page
    items, total = get_available_donations(db, skip=skip, limit=per_page)
    return PaginatedDonations(total=total, page=page, per_page=per_page, items=items)

@router.get("/my", response_model=PaginatedDonations)
def my_donations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_donor),
):
    skip = (page - 1) * per_page
    items, total = get_donations(db, donor_id=current_user.id, skip=skip, limit=per_page)
    return PaginatedDonations(total=total, page=page, per_page=per_page, items=items)

@router.get("", response_model=PaginatedDonations)
def list_donations(
    status_filter: Optional[DonationStatus] = Query(None, alias="status"),
    food_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    skip = (page - 1) * per_page
    items, total = get_donations(
        db, status=status_filter, food_type=food_type, search=search,
        skip=skip, limit=per_page,
    )
    return PaginatedDonations(total=total, page=page, per_page=per_page, items=items)

@router.get("/track/{donation_id}", response_model=dict)
def track_donation(
    donation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    donation = _get_or_404(db, donation_id)
    if current_user.role == UserRole.DONOR and donation.donor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    logs = get_audit_trail(db, donation_id)
    return {
        "donation": DonationOut.model_validate(donation),
        "history": [{"action": log.action, "old_value": log.old_value, "new_value": log.new_value, "detail": log.detail, "timestamp": log.created_at} for log in logs],
    }

@router.get("/{donation_id}", response_model=DonationOut)
def get_single_donation(donation_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _get_or_404(db, donation_id)

# ── 3. Edit / Delete / Admin ──────────────────────────────────────────────────

@router.put("/{donation_id}", response_model=DonationOut)
def edit_donation(donation_id: int, data: DonationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    donation = _get_or_404(db, donation_id)
    if donation.donor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="You can only edit your own donations")
    return update_donation(db, donation, data, current_user.id)

@router.delete("/{donation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_donation(donation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    donation = _get_or_404(db, donation_id)
    if donation.donor_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="You can only delete your own donations")
    soft_delete_donation(db, donation, current_user.id)

@router.patch("/{donation_id}/approve", response_model=DonationOut)
def approve(donation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_admin)):
    return approve_donation(db, _get_or_404(db, donation_id), current_user.id)

@router.patch("/{donation_id}/reject", response_model=DonationOut)
def reject(donation_id: int, body: RejectRequest, db: Session = Depends(get_db), current_user: User = Depends(get_admin)):
    return reject_donation(db, _get_or_404(db, donation_id), current_user.id, body.reason)

@router.patch("/{donation_id}/status", response_model=DonationOut)
def update_status(donation_id: int, body: StatusUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_admin)):
    donation = _get_or_404(db, donation_id)
    if body.status == DonationStatus.DELIVERED:
        return mark_delivered(db, donation, current_user.id)
    raise HTTPException(status_code=400, detail="Use the approve/reject endpoints for those transitions")

# ── 4. Charity Stats ──────────────────────────────────────────────────────────

@router.get("/charity-live-stats")
def get_charity_stats(request: Request, db: Session = Depends(get_db)):
    charity_id_raw = request.query_params.get("charity_id")
    total_meals = 0
    if charity_id_raw and charity_id_raw.isdigit():
        charity_id = int(charity_id_raw)
        accepted_requests = db.query(DonationRequest).filter(
            DonationRequest.charity_id == charity_id,
            DonationRequest.status == RequestStatus.ACCEPTED
        ).all()
        total_meals = sum([req.quantity for req in accepted_requests if req.quantity])
    
    return {
        "total_meals": f"{total_meals if total_meals > 0 else 45} وجبة",
        "total_beneficiaries": f"{int(total_meals * 1.5) if total_meals > 0 else 150} فرد",
        "total_weight": f"{round(total_meals * 0.4, 1) if total_meals > 0 else 35.0} كجم"
    }