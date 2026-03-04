from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .. import models, schemas
from ..database import get_db
from ..utils.dependencies import get_current_user, get_current_admin_user
from ..services.ai_service import semantic_search, get_recommendations, process_chat, generate_book_embedding

router = APIRouter(prefix="/ai", tags=["ai"])

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    reply: str

@router.get("/search", response_model=List[schemas.BookRead])
def search_books(
    query: str,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db)
) -> Any:
    return semantic_search(query, db, limit=limit)

@router.get("/recommendations", response_model=List[schemas.BookRead])
def user_recommendations(
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    return get_recommendations(current_user.id, db, limit)

@router.post("/chat", response_model=ChatResponse)
def ask_chatbot(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    reply = process_chat(request.query, current_user.id, db)
    return ChatResponse(reply=reply)

@router.post("/reindex", response_model=dict)
def reindex_all_books(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
) -> Any:
    books = db.query(models.Book).all()
    count = 0
    for book in books:
        generate_book_embedding(book, db)
        count += 1
    return {"message": f"Successfully re-indexed {count} books"}
