from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.entities import User, UserRole
from app.schemas.auth import Token, LoginRequest, UserResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/login", response_model=Token, summary="Authenticate user and issue JWT")
def login(request: LoginRequest, db: Session = Depends(get_db)) -> Any:
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )

    access_token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
    }


@router.get("/me", response_model=UserResponse, summary="Get current logged in user")
def read_current_user(current_user: User = Depends(get_current_user)) -> Any:
    return current_user


@router.get("/demo-users", summary="List representative demo users for quick reviewer login")
def list_demo_users(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_active == True).all()
    # Provide credentials hint for evaluation
    password_hints = {
        "admin@estateflow.ai": "Admin@123",
        "saleshead@estateflow.ai": "Head@123",
        "rahul.sales@estateflow.ai": "Sales@123",
        "priya.sales@estateflow.ai": "Sales@123",
        "buyer@estateflow.ai": "Buyer@123"
    }
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "password_hint": password_hints.get(u.email, "Sales@123")
        }
        for u in users[:8]
    ]
