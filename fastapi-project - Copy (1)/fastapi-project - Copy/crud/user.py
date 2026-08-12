from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.user import User, UserRole
from schemas.user import UserCreate, UserUpdate
from core.security import hash_password


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_all_users(
    db: Session,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[User], int]:
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    total = q.count()
    users = q.offset(skip).limit(limit).all()
    return users, total


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        address=data.address,
        phone_number=data.phone_number,
        role=data.role,
        latitude=data.latitude,
        longitude=data.longitude,
        photo_url=data.photo_url,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user: User) -> User:
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


def get_users_by_role(db: Session, role: UserRole) -> list[User]:
    return db.query(User).filter(User.role == role, User.is_active == True).all()


def get_nearby_users(
    db: Session, role: UserRole, lat: float, lon: float, limit: int = 10
) -> list[User]:
    """Return users of a given role sorted by Euclidean distance (proxy for haversine)."""
    users = (
        db.query(User)
        .filter(
            User.role == role,
            User.is_active == True,
            User.latitude.isnot(None),
            User.longitude.isnot(None),
        )
        .all()
    )
    # Sort by simple Euclidean distance (good enough for SQLite without PostGIS)
    users.sort(
        key=lambda u: (u.latitude - lat) ** 2 + (u.longitude - lon) ** 2
    )
    return users[:limit]
