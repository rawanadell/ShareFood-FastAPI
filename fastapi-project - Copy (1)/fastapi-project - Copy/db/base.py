from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone
from db.session import Base

class Base(DeclarativeBase):
    pass

def utcnow():
    return datetime.now(timezone.utc)