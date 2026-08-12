from sqlalchemy.orm import Session
from models.notification import Notification


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    donation_id: int = None,
    location: str = None,
    is_interactive: bool = False,
    security_code: str = None,
) -> Notification:
    """Create a new notification for a user"""
    notification = Notification(
        user_id=user_id,
        donation_id=donation_id,
        title=title,
        message=message,
        location=location,
        is_interactive=is_interactive,
        security_code=security_code,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
