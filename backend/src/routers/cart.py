from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=List[schemas.CartItemRead])
def get_cart(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
) -> Any:
    return (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == current_user.id)
        .all()
    )


@router.post(
    "/", response_model=schemas.CartItemRead, status_code=status.HTTP_201_CREATED
)
def add_to_cart(
    item_in: schemas.CartItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> Any:
    book = db.query(models.Book).filter(models.Book.id == item_in.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing_item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.user_id == current_user.id,
            models.CartItem.book_id == item_in.book_id,
        )
        .first()
    )

    if existing_item:
        existing_item.quantity += item_in.quantity
        db.commit()
        db.refresh(existing_item)
        return existing_item

    new_item = models.CartItem(user_id=current_user.id, **item_in.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.put("/{item_id}", response_model=schemas.CartItemRead)
def update_cart_item(
    item_id: int,
    item_in: schemas.CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> Any:
    item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.id == item_id, models.CartItem.user_id == current_user.id
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    item.quantity = item_in.quantity
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> Any:
    item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.id == item_id, models.CartItem.user_id == current_user.id
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(item)
    db.commit()
