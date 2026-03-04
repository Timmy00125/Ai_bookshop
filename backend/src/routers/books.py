from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils.dependencies import get_current_admin_user

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=List[schemas.BookRead])
def get_books(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    genre: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = Query(
        "newest", pattern="^(price|newest|rating|popularity)$"
    ),
) -> Any:
    query = db.query(models.Book)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                models.Book.title.ilike(search_filter),
                models.Book.author.ilike(search_filter),
                models.Book.description.ilike(search_filter),
            )
        )
    if genre:
        query = query.filter(models.Book.genre.ilike(f"%{genre}%"))
    if min_price is not None:
        query = query.filter(models.Book.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Book.price <= max_price)

    if sort_by == "price":
        query = query.order_by(asc(models.Book.price))
    elif sort_by == "rating":
        query = query.order_by(desc(models.Book.average_rating))
    elif sort_by == "popularity":
        query = query.order_by(desc(models.Book.stock_count))  # simplified fallback
    else:  # newest
        query = query.order_by(desc(models.Book.created_at))

    return query.offset(skip).limit(limit).all()


@router.get("/{book_id}", response_model=schemas.BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> Any:
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=schemas.BookRead, status_code=status.HTTP_201_CREATED)
def create_book(
    book_in: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    book = models.Book(**book_in.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@router.put("/{book_id}", response_model=schemas.BookRead)
def update_book(
    book_id: int,
    book_in: schemas.BookUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = book_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(book, key, value)

    db.commit()
    db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user),
) -> Any:
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(book)
    db.commit()
