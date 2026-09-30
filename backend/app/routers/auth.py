"""Authentication router providing user registration, JWT login, and refresh token rotation."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LoginRequest, RefreshRequest, TokenResponse, UserCreate
from app.security import (
    create_access_token,
    create_refresh_token,
    rotate_refresh_token,
    verify_password,
)
from app.services.audit_service import event_bus
from app.services.db_service import db_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    """Register a new user account and return an initial JWT access and refresh token pair."""
    db_service.seed_initial_data(db)
    existing = db_service.get_user_by_username(db, payload.username)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    user = db_service.create_user(db, payload)
    event_bus.publish(
        db,
        {
            "actor": user.username,
            "action": "USER_REGISTERED",
            "resource": user.username,
            "details": {"role": user.role, "org_id": user.org_id},
        },
    )
    return TokenResponse(
        access_token=create_access_token(user.username, user.role, user.org_id),
        refresh_token=create_refresh_token(user.username, user.role, user.org_id),
        role=user.role,
        org_id=user.org_id,
    )


@router.post("/login", response_model=TokenResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate user credentials with bcrypt and issue a 15-min access + 7-day refresh token."""
    db_service.seed_initial_data(db)
    user = db_service.get_user_by_username(db, payload.username)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    event_bus.publish(
        db,
        {
            "actor": user.username,
            "action": "USER_LOGIN_SUCCESS",
            "resource": "AUTH",
            "details": {"role": user.role},
        },
    )
    return TokenResponse(
        access_token=create_access_token(user.username, user.role, user.org_id),
        refresh_token=create_refresh_token(user.username, user.role, user.org_id),
        role=user.role,
        org_id=user.org_id,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_user_token(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Rotate a valid refresh token and return a new access and refresh token pair."""
    access_tok, refresh_tok = rotate_refresh_token(payload.refresh_token)
    from app.security import decode_token

    claims = decode_token(access_tok)
    event_bus.publish(
        db,
        {
            "actor": str(claims["sub"]),
            "action": "JWT_REFRESH_ROTATED",
            "resource": "AUTH",
            "details": {"role": claims["role"]},
        },
    )
    return TokenResponse(
        access_token=access_tok,
        refresh_token=refresh_tok,
        role=str(claims["role"]),
        org_id=claims.get("org_id"),
    )
