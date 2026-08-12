from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.session import get_db
from core.dependencies import get_admin
from schemas.report import generate_report
from crud.user import get_all_users
from crud.donation import get_donations
from crud.request import get_requests
from models.user import User
from schemas.report import AdminReport
from schemas.user import UserOut
from schemas.donation import DonationOut, PaginatedDonations
from schemas.request import RequestOut, PaginatedRequests

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/reports", response_model=AdminReport)
def reports(db: Session = Depends(get_db), _: User = Depends(get_admin)):
    return generate_report(db)


@router.get("/users", response_model=dict)
def admin_list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin),
):
    skip = (page - 1) * per_page
    users, total = get_all_users(db, skip=skip, limit=per_page)
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [UserOut.model_validate(u) for u in users],
    }


@router.get("/donations", response_model=PaginatedDonations)
def admin_list_donations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin),
):
    skip = (page - 1) * per_page
    items, total = get_donations(db, skip=skip, limit=per_page)
    return PaginatedDonations(total=total, page=page, per_page=per_page, items=items)


@router.get("/requests", response_model=PaginatedRequests)
def admin_list_requests(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin),
):
    skip = (page - 1) * per_page
    items, total = get_requests(db, skip=skip, limit=per_page)
    return PaginatedRequests(total=total, page=page, per_page=per_page, items=items)
