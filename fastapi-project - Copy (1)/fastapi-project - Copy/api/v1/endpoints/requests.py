from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from db.session import get_db
from core.dependencies import get_current_user, get_charity, get_admin
from crud.request import create_request, get_request, get_requests, update_request_status
from models.user import User, UserRole
from models.request import RequestStatus
from schemas.request import RequestCreate, RequestOut, RequestStatusUpdate, PaginatedRequests

router = APIRouter(prefix="/requests", tags=["Requests"])


def _get_or_404(db, request_id):
    r = get_request(db, request_id)
    if not r:
        raise HTTPException(status_code=404, detail="Request not found")
    return r


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def submit_request(
    data: RequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_charity),
):
    return create_request(db, data, current_user.id)


@router.get("/my", response_model=PaginatedRequests)
def my_requests(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_charity),
):
    skip = (page - 1) * per_page
    items, total = get_requests(db, charity_id=current_user.id, skip=skip, limit=per_page)
    return PaginatedRequests(total=total, page=page, per_page=per_page, items=items)


@router.get("/track/{request_id}", response_model=RequestOut)
def track_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = _get_or_404(db, request_id)
    if current_user.role == UserRole.CHARITY and req.charity_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return req


@router.get("", response_model=PaginatedRequests)
def list_requests(
    req_status: Optional[RequestStatus] = Query(None, alias="status"),
    donation_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin),
):
    skip = (page - 1) * per_page
    items, total = get_requests(
        db, req_status=req_status, donation_id=donation_id, skip=skip, limit=per_page
    )
    return PaginatedRequests(total=total, page=page, per_page=per_page, items=items)


@router.get("/{request_id}", response_model=RequestOut)
def get_single_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = _get_or_404(db, request_id)
    if current_user.role == UserRole.CHARITY and req.charity_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return req


@router.patch("/{request_id}/status", response_model=RequestOut)
def change_request_status(
    request_id: int,
    body: RequestStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin),
):
    req = _get_or_404(db, request_id)
    return update_request_status(db, req, body.status)
