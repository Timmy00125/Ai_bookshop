from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, condecimal

from .models import OrderStatus, UserRole


# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Book Schemas ---
class BookBase(BaseModel):
    title: str
    author: str
    price: condecimal(gt=0, decimal_places=2)
    description: Optional[str] = None
    genre: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[datetime] = None
    cover_image_url: Optional[str] = None
    stock_count: Optional[int] = 0


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    price: Optional[condecimal(gt=0, decimal_places=2)] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    stock_count: Optional[int] = None
    cover_image_url: Optional[str] = None


class BookRead(BookBase):
    id: int
    average_rating: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Cart Schemas ---
class CartItemCreate(BaseModel):
    book_id: int
    quantity: int = Field(default=1, gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemRead(BaseModel):
    id: int
    book_id: int
    quantity: int
    added_at: datetime
    book: BookRead

    class Config:
        from_attributes = True


# --- Order Schemas ---
class OrderItemRead(BaseModel):
    id: int
    book_id: int
    quantity: int
    unit_price: Decimal
    book: BookRead

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    id: int
    user_id: int
    total_price: Decimal
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemRead] = []

    class Config:
        from_attributes = True
