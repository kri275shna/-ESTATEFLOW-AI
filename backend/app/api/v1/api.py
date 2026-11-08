from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, leads, chat, bookings, handoffs, analytics, admin

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Chat"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(handoffs.router, prefix="/handoffs", tags=["Sales Handoffs"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Configuration"])
