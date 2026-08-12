from fastapi import APIRouter
from api.v1.endpoints import notifications
from api.v1.endpoints import (
    auth, 
    users, 
    donations, 
    requests, 
    volunteers, 
    admin, 
    notifications  
)

api_router = APIRouter()

# ✅ شيلنا الـ prefix من كل الروترز لمنع تكرار الكلمات في الـ URLs وضمان التوافق التام مع فلاتر
api_router.include_router(auth.router, tags=["Auth"]) 
api_router.include_router(users.router, tags=["Users"]) 
api_router.include_router(donations.router, tags=["Donations"])
api_router.include_router(requests.router, tags=["Requests"])
api_router.include_router(volunteers.router, tags=["Volunteers"])
api_router.include_router(admin.router, tags=["Admin"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])