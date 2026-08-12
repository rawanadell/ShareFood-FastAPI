from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.security import decode_token
from db.session import get_db
from models.user import User, UserRole

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_role(*roles: UserRole):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {[r.value for r in roles]}",
            )
        return current_user
    return checker


# Convenience role guards
def get_admin(user: User = Depends(require_role(UserRole.ADMIN))) -> User:
    return user

def get_donor(user: User = Depends(require_role(UserRole.DONOR))) -> User:
    return user

def get_charity(user: User = Depends(require_role(UserRole.CHARITY))) -> User:
    return user

def get_volunteer(user: User = Depends(require_role(UserRole.VOLUNTEER))) -> User:
    return user

def get_admin_or_donor(
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.DONOR))
) -> User:
    return user
