from datetime import datetime, timedelta, timezone
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])


# --- User Management ---


class UserUpdateAdmin(BaseModel):
    role: models.UserRole | None = None
    is_active: bool | None = None


@router.get("/users", response_model=List[schemas.UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=schemas.UserRead)
def update_user(
    user_id: int,
    user_in: UserUpdateAdmin,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=400, detail="Cannot modify your own account from admin panel"
        )

    update_data = user_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Response:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=400, detail="Cannot delete your own account"
        )

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Analytics ---


class AnalyticsResponse(BaseModel):
    total_users: int
    total_books: int
    total_orders: int
    total_revenue: float
    orders_by_status: dict
    users_by_role: dict
    recent_signups: int


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    total_users = db.query(models.User).count()
    total_books = db.query(models.Book).count()
    total_orders = db.query(models.Order).count()

    revenue = db.query(func.sum(models.Order.total_price)).scalar()
    total_revenue = float(revenue) if revenue else 0.0

    # Orders by status
    order_statuses = (
        db.query(models.Order.status, func.count(models.Order.id))
        .group_by(models.Order.status)
        .all()
    )
    orders_by_status = {s.value: 0 for s in models.OrderStatus}
    for status_val, count in order_statuses:
        orders_by_status[status_val.value] = count

    # Users by role
    user_roles = (
        db.query(models.User.role, func.count(models.User.id))
        .group_by(models.User.role)
        .all()
    )
    users_by_role = {r.value: 0 for r in models.UserRole}
    for role_val, count in user_roles:
        users_by_role[role_val.value] = count

    # Recent signups (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_signups = (
        db.query(models.User)
        .filter(models.User.created_at >= week_ago)
        .count()
    )

    return AnalyticsResponse(
        total_users=total_users,
        total_books=total_books,
        total_orders=total_orders,
        total_revenue=total_revenue,
        orders_by_status=orders_by_status,
        users_by_role=users_by_role,
        recent_signups=recent_signups,
    )
