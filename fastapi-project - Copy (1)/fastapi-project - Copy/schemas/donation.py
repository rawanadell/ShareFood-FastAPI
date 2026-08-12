from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from models.donation import DonationStatus
from schemas.user import UserOut

# 1. كلاسات الـ Input
class DonationCreate(BaseModel):
    title: str
    description: Optional[str] = None
    food_type: str
    quantity: int
    expiry_time: Optional[str] = "6 ساعات"
    address: Optional[str] = None
    photo_url: Optional[str] = None 

    @field_validator("title", "food_type")
    @classmethod
    def not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be a positive integer")
        return v

class DonationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    food_type: Optional[str] = None
    quantity: Optional[int] = None
    expiry_time: Optional[str] = None
    address: Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Quantity must be a positive integer")
        return v

# 2. كلاسات الـ Output
class DonationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: Optional[str]
    food_type: str
    quantity: int
    status: DonationStatus
    rejection_reason: Optional[str]
    donor_id: int
    approved_by: Optional[int]
    date_created: datetime
    updated_at: datetime
    expiry_time: Optional[str] = None
    address: Optional[str] = None
    photo_url: Optional[str] = None 

class DonationDetailOut(DonationOut):
    donor: Optional[UserOut] = None

# 3. كلاسات العمليات
class RejectRequest(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Rejection reason cannot be empty")
        return v.strip()

class StatusUpdateRequest(BaseModel):
    status: DonationStatus

class PaginatedDonations(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[DonationOut]