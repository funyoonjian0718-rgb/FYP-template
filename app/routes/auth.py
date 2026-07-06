from datetime import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import PasswordResetToken, User
from app.db.session import get_db


router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        type2_diabetes=payload.type2_diabetes,
        age=payload.age,
        weight_kg=payload.weight_kg,
        activity_level=payload.activity_level,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserProfileResponse)
def me(user: User = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        type2_diabetes=user.type2_diabetes,
        age=user.age,
        weight_kg=user.weight_kg,
        activity_level=user.activity_level,
        created_at=user.created_at,
    )


@router.get("/profile", response_model=UserProfileResponse)
def profile(user: User = Depends(get_current_user)) -> UserProfileResponse:
    return me(user)


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    payload: UserProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    if payload.type2_diabetes is not None:
        user.type2_diabetes = payload.type2_diabetes
    if payload.age is not None:
        user.age = payload.age
    if payload.weight_kg is not None:
        user.weight_kg = payload.weight_kg
    if payload.activity_level is not None:
        user.activity_level = payload.activity_level
    db.commit()
    db.refresh(user)
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        type2_diabetes=user.type2_diabetes,
        age=user.age,
        weight_kg=user.weight_kg,
        activity_level=user.activity_level,
        created_at=user.created_at,
    )


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        # avoid account enumeration
        return {"ok": True}

    token = secrets.token_urlsafe(32)
    prt = PasswordResetToken(user_id=user.id, token=token, used=False, created_at=datetime.utcnow())
    db.add(prt)
    db.commit()

    # Demo-only: return token directly (no email flow)
    return {"ok": True, "reset_token": token}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict:
    prt = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token == payload.token))
    if not prt or prt.used:
        raise HTTPException(status_code=400, detail="Invalid or used reset token")

    user = db.scalar(select(User).where(User.id == prt.user_id))
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    user.password_hash = hash_password(payload.new_password)
    prt.used = True
    db.commit()
    return {"ok": True}

