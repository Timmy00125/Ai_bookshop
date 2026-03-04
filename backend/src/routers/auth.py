from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.dependencies import get_current_active_user
from ..utils.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserRead)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)) -> Any:
    # Check if username or email exists
    user = (
        db.query(models.User)
        .filter(
            (models.User.email == user_in.email)
            | (models.User.username == user_in.username)
        )
        .first()
    )
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username or email already exists in the system.",
        )

    # Determine role (first user becomes admin, rest are user)
    count = db.query(models.User).count()
    role = models.UserRole.admin if count == 0 else models.UserRole.user

    user_obj = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=role,
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj


@router.post("/login")
def login(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = (
        db.query(models.User).filter(models.User.username == form_data.username).first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    return {
        "access_token": create_access_token(
            data={"sub": user.username, "role": user.role.value},
            expires_delta=access_token_expires,
        ),
        "token_type": "bearer",
    }


@router.get("/me", response_model=schemas.UserRead)
def read_current_user(
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    return current_user
