from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.dependencies import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/reading-history", response_model=List[schemas.BookRead])
def get_reading_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    # Get the most recent browsing event per book for this user
    subq = (
        db.query(
            models.UserBrowsingHistory.book_id,
            func.max(models.UserBrowsingHistory.timestamp).label("latest"),
        )
        .filter(models.UserBrowsingHistory.user_id == current_user.id)
        .group_by(models.UserBrowsingHistory.book_id)
        .subquery()
    )

    results = (
        db.query(models.Book)
        .join(subq, models.Book.id == subq.c.book_id)
        .order_by(subq.c.latest.desc())
        .limit(limit)
        .all()
    )

    return results
