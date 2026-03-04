from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from .. import models, schemas
from ..database import get_db
from ..utils.dependencies import get_current_user, get_current_admin_user

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/", response_model=List[schemas.OrderRead])
def get_orders(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)) -> Any:
    return db.query(models.Order).filter(models.Order.user_id == current_user.id).order_by(models.Order.created_at.desc()).all()

@router.post("/checkout", response_model=schemas.OrderRead, status_code=status.HTTP_201_CREATED)
def checkout(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)) -> Any:
    cart_items = db.query(models.CartItem).filter(models.CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
        
    total_price = Decimal("0.0")
    for item in cart_items:
        total_price += item.book.price * item.quantity
        
    order = models.Order(
        user_id=current_user.id,
        total_price=total_price,
        status=models.OrderStatus.completed # Simulated checkout automatically completes
    )
    db.add(order)
    db.flush() # flush to get order.id
    
    for item in cart_items:
        order_item = models.OrderItem(
            order_id=order.id,
            book_id=item.book_id,
            quantity=item.quantity,
            unit_price=item.book.price
        )
        db.add(order_item)
        
        # Log purchase history
        history = models.UserBrowsingHistory(
            user_id=current_user.id,
            book_id=item.book_id,
            event_type=models.HistoryEventType.purchase
        )
        db.add(history)
        
        # Remove from cart
        db.delete(item)
        
    db.commit()
    db.refresh(order)
    return order

@router.get("/all", response_model=List[schemas.OrderRead])
def get_all_orders_admin(db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin_user)) -> Any:
    return db.query(models.Order).order_by(models.Order.created_at.desc()).all()
