from typing import List

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from .. import models

# Load the sentence transformer model globally (lazy loading can also be done)
_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_embedding(text: str) -> List[float]:
    model = get_model()
    return model.encode(text).tolist()


def generate_book_embedding(book: models.Book, db: Session):
    text_to_embed = f"{book.title} {book.author} {book.genre} {book.description or ''}"
    vector = get_embedding(text_to_embed)

    embedding_record = (
        db.query(models.BookEmbedding)
        .filter(models.BookEmbedding.book_id == book.id)
        .first()
    )
    if embedding_record:
        embedding_record.embedding = vector
    else:
        embedding_record = models.BookEmbedding(
            book_id=book.id, embedding=vector, model_version="all-MiniLM-L6-v2"
        )
        db.add(embedding_record)
    db.commit()


def semantic_search(query: str, db: Session, limit: int = 5) -> List[models.Book]:
    query_vector = get_embedding(query)

    # Use pgvector's cosine distance `<=>` operator
    # The order_by sorts ascending, so smallest distance is best
    results = (
        db.query(models.BookEmbedding)
        .order_by(models.BookEmbedding.embedding.cosine_distance(query_vector))
        .limit(limit)
        .all()
    )

    return [r.book for r in results if r.book]


def get_recommendations(user_id: int, db: Session, limit: int = 6) -> List[models.Book]:
    history = (
        db.query(models.UserBrowsingHistory)
        .filter(models.UserBrowsingHistory.user_id == user_id)
        .order_by(models.UserBrowsingHistory.timestamp.desc())
        .limit(3)
        .all()
    )

    if not history:
        # Fallback to highly rated books
        return (
            db.query(models.Book)
            .order_by(models.Book.average_rating.desc())
            .limit(limit)
            .all()
        )

    recent_book_ids = [h.book_id for h in history]
    embeddings = (
        db.query(models.BookEmbedding)
        .filter(models.BookEmbedding.book_id.in_(recent_book_ids))
        .all()
    )

    if not embeddings:
        return (
            db.query(models.Book)
            .order_by(models.Book.average_rating.desc())
            .limit(limit)
            .all()
        )

    # Calculate average vector for user's recent interests
    avg_vector = [0.0] * len(embeddings[0].embedding)
    for embed in embeddings:
        for i, val in enumerate(embed.embedding):
            avg_vector[i] += val

    avg_vector = [val / len(embeddings) for val in avg_vector]

    # Find nearest neighbors excluding already interacted ones
    results = (
        db.query(models.BookEmbedding)
        .filter(models.BookEmbedding.book_id.notin_(recent_book_ids))
        .order_by(models.BookEmbedding.embedding.cosine_distance(avg_vector))
        .limit(limit)
        .all()
    )

    return [r.book for r in results if r.book]


def process_chat(query: str, user_id: int, db: Session) -> str:
    # RAG pipeline: retrieve context
    context_books = semantic_search(query, db, limit=3)

    # Mock LLM generation
    if not context_books:
        return (
            "I'm sorry, I couldn't find any books that match your interest right now."
        )

    titles = [f"'{b.title}' by {b.author}" for b in context_books]
    response = (
        f"Based on your query, I found some great recommendations from our catalog! "
        f"You might enjoy {', '.join(titles)}. Would you like to read a summary of any of these?"
    )
    return response
