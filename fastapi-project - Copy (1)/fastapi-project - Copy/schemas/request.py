from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

from models.request import RequestStatus


class RequestCreate(BaseModel):
    donation_id: int
    food_type: str
    quantity: int
    notes: Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be a positive integer")
        return v

    @field_validator("food_type")
    @classmethod
    def food_type_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Food type cannot be empty")
        return v.strip()


class RequestStatusUpdate(BaseModel):
    status: RequestStatus


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    food_type: str
    quantity: int
    status: RequestStatus
    notes: Optional[str]
    charity_id: int
    donation_id: int
    date_requested: datetime
    updated_at: datetime


class PaginatedRequests(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[RequestOut]
