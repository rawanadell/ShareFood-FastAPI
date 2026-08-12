from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import time
from typing import List

from core.config import settings
from api.v1.router import api_router
from db.session import engine, get_db
from db.base import Base
import models 

# Import all models for SQLAlchemy
import models  # noqa: F401

def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Backend API for the Food Donation Platform",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request timing middleware
    @application.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.time() - start:.4f}s"
        return response

    # Global exception handler
    @application.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": type(exc).__name__},
        )

    # ✅ التعديل الأهم: إضافة الـ prefix هنا عشان يغطي كل الروابط (Auth, Users, Notifications)
    application.include_router(api_router, prefix="/api/v1")

    @application.get("/", tags=["Health"])
    def health_check():
        return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}

    return application

app = create_app()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

# ❌ شيلنا دالة get_notifications من هنا لأنها موجودة فعلاً في api/v1/endpoints/notifications.py
# وكدة المسارات هتبقى نظيفة ومافيش تضارب.
from fastapi.staticfiles import StaticFiles # تأكدي من هذا الاستيراد

# ضعي هذا السطر بعد تعريف app وقبل تشغيل السيرفر
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")