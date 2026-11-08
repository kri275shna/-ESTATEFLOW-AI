from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/health", summary="System Health and Status Check")
def health_check(db: Session = Depends(get_db)):
    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "client": settings.DEVELOPER_NAME,
        "location": settings.LOCATION,
        "ai_engine": "live_llm" if (settings.GEMINI_API_KEY or settings.OPENAI_API_KEY) else "grounded_deterministic_fallback",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
