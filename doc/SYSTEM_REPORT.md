# AI-Enhanced Online Bookshop — System Report

**Project:** Design and Implementation of an AI-Enhanced Online Bookshop
**Author:** Nwamgbowo Bruno Nwachukwu (VUG/CSC/22/7793)
**Institution:** Veritas University Abuja — Dept. of Computer and Information Technology
**Date:** May 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [How the AI Works](#2-how-the-ai-works)
   - 2.1 [Embedding Model](#21-embedding-model)
   - 2.2 [Semantic Search Engine](#22-semantic-search-engine)
   - 2.3 [Recommendation Engine](#23-recommendation-engine)
   - 2.4 [AI Chatbot (RAG Pipeline)](#24-ai-chatbot-rag-pipeline)
   - 2.5 [Embedding Generation & Storage](#25-embedding-generation--storage)
   - 2.6 [AI Service Architecture](#26-ai-service-architecture)
3. [How the Admin Dashboard Works](#3-how-the-admin-dashboard-works)
   - 3.1 [Authentication & Access Control](#31-authentication--access-control)
   - 3.2 [Analytics Overview](#32-analytics-overview)
   - 3.3 [Book Management (CRUD)](#33-book-management-crud)
   - 3.4 [Order Management](#34-order-management)
   - 3.5 [User Management](#35-user-management)
   - 3.6 [Search Vector Reindexing](#36-search-vector-reindexing)
   - 3.7 [Frontend Implementation Details](#37-frontend-implementation-details)
4. [How Semantic Search Works](#4-how-semantic-search-works)
   - 4.1 [What is Semantic Search?](#41-what-is-semantic-search)
   - 4.2 [The Embedding Pipeline](#42-the-embedding-pipeline)
   - 4.3 [Vector Similarity with pgvector](#43-vector-similarity-with-pgvector)
   - 4.4 [Query Processing Flow](#44-query-processing-flow)
   - 4.5 [Cosine Distance Explained](#45-cosine-distance-explained)
   - 4.6 [Fallback Mechanism](#46-fallback-mechanism)
   - 4.7 [Frontend Search Modes](#47-frontend-search-modes)
5. [How Books Get Into the System](#5-how-books-get-into-the-system)
   - 5.1 [Admin Manual Entry](#51-admin-manual-entry)
   - 5.2 [Seed Script (Small Dataset)](#52-seed-script-small-dataset)
   - 5.3 [Bulk Seed Script (1000+ Books)](#53-bulk-seed-script-1000-books)
   - 5.4 [Book Data Model](#54-book-data-model)
   - 5.5 [Automatic Embedding on Ingestion](#55-automatic-embedding-on-ingestion)
6. [Tech Stack Summary](#6-tech-stack-summary)
7. [Database Schema](#7-database-schema)
8. [API Architecture](#8-api-architecture)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Security Implementation](#10-security-implementation)
11. [Deployment & Infrastructure](#11-deployment--infrastructure)

---

## 1. System Overview

The AI-Enhanced Online Bookshop is a full-stack web application that combines standard e-commerce functionality (browsing, cart, checkout) with three core AI-powered features:

- **Semantic Search** — Users search using natural language queries like "books about African history for students" instead of exact keyword matching.
- **Personalized Recommendations** — The system suggests books based on a user's browsing and purchase history using vector similarity.
- **Conversational AI Chatbot** — A virtual assistant that uses a RAG (Retrieval-Augmented Generation) pipeline to answer user queries and recommend books.

The system is built as a **React + FastAPI** application backed by **PostgreSQL with pgvector** for vector storage and similarity search. The AI layer uses **Sentence-BERT** for generating text embeddings locally without requiring external API calls.

---

## 2. How the AI Works

The AI subsystem is the core differentiator of this bookshop. It consists of four interconnected components: the embedding model, semantic search, the recommendation engine, and the chatbot.

### 2.1 Embedding Model

**Location:** `backend/src/services/ai_service.py:12-21`

The system uses the **`all-MiniLM-L6-v2`** model from the `sentence-transformers` library. This model was chosen because:

- It produces **384-dimensional** vectors, which are compact and fast to compare.
- It runs **entirely locally** — no external API calls or API keys required.
- It is optimized for **semantic similarity tasks** and performs well on short-to-medium text passages.
- It is lightweight enough to run on modest hardware.

```python
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model
```

The model is **lazily loaded** on first use. Once loaded, it stays in memory for the lifetime of the application process, avoiding repeated model loading overhead.

The `get_embedding()` function takes any text string and returns a 384-float vector:

```python
def get_embedding(text: str) -> List[float]:
    model = get_model()
    return model.encode(text).tolist()
```

### 2.2 Semantic Search Engine

**Location:** `backend/src/services/ai_service.py:43-55`

Semantic search allows users to find books using natural language. The process works as follows:

1. **User enters a query** (e.g., "beginner books on machine learning").
2. The query text is converted into a **384-dimensional vector** using the Sentence-BERT model.
3. The system performs a **cosine distance** search against all stored book embeddings in the database using pgvector's `<=>` operator.
4. Results are sorted by **ascending cosine distance** (smallest distance = most similar).
5. The top N most similar books are returned.

```python
def semantic_search(query: str, db: Session, limit: int = 5) -> List[models.Book]:
    query_vector = get_embedding(query)
    results = (
        db.query(models.BookEmbedding)
        .order_by(models.BookEmbedding.embedding.cosine_distance(query_vector))
        .limit(limit)
        .all()
    )
    return [r.book for r in results if r.book]
```

The search is exposed via the `GET /ai/search` endpoint:

```python
@router.get("/search", response_model=List[schemas.BookRead])
def search_books(query: str, limit: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    return semantic_search(query, db, limit=limit)
```

### 2.3 Recommendation Engine

**Location:** `backend/src/services/ai_service.py:58-108`

The recommendation system is **content-based**, using vector similarity to find books similar to what the user has recently interacted with. The algorithm works as follows:

1. **Fetch the user's last 3 browsing events** from `UserBrowsingHistory` (views, cart adds, purchases).
2. If no history exists, **fall back to the highest-rated books** in the catalog.
3. Retrieve the **embedding vectors** for the recently interacted books.
4. Compute an **average vector** by element-wise averaging all the retrieved embeddings. This represents the user's "interest profile."
5. Perform a **cosine distance search** against all book embeddings, **excluding books the user has already interacted with**.
6. Return the top N nearest books as recommendations.

```python
def get_recommendations(user_id: int, db: Session, limit: int = 6) -> List[models.Book]:
    history = (
        db.query(models.UserBrowsingHistory)
        .filter(models.UserBrowsingHistory.user_id == user_id)
        .order_by(models.UserBrowsingHistory.timestamp.desc())
        .limit(3)
        .all()
    )

    if not history:
        return db.query(models.Book).order_by(models.Book.average_rating.desc()).limit(limit).all()

    recent_book_ids = [h.book_id for h in history]
    embeddings = (
        db.query(models.BookEmbedding)
        .filter(models.BookEmbedding.book_id.in_(recent_book_ids))
        .all()
    )

    if not embeddings:
        return db.query(models.Book).order_by(models.Book.average_rating.desc()).limit(limit).all()

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
```

**User interaction tracking:** Events are logged in the `UserBrowsingHistory` table with three event types:
- `view` — When a user views a book detail page.
- `cart_add` — When a user adds a book to their cart.
- `purchase` — When a user completes checkout.

The `purchase` event is logged during the checkout process in `backend/src/routers/orders.py:62-66`.

The recommendations endpoint is `GET /ai/recommendations` and requires authentication:

```python
@router.get("/recommendations", response_model=List[schemas.BookRead])
def user_recommendations(
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return get_recommendations(current_user.id, db, limit)
```

### 2.4 AI Chatbot (RAG Pipeline)

**Location:** `backend/src/services/ai_service.py:111-126`

The chatbot implements a simplified **Retrieval-Augmented Generation (RAG)** pipeline:

1. **User sends a message** (e.g., "Can you recommend a good thriller?").
2. The message is passed to `semantic_search()` to retrieve the **top 3 most relevant books** from the catalog.
3. The retrieved books are used as **context** to construct a response.
4. The response includes the book titles and authors in a friendly, conversational format.

```python
def process_chat(query: str, user_id: int, db: Session) -> str:
    context_books = semantic_search(query, db, limit=3)

    if not context_books:
        return "I'm sorry, I couldn't find any books that match your interest right now."

    titles = [f"'{b.title}' by {b.author}" for b in context_books]
    response = (
        f"Based on your query, I found some great recommendations from our catalog! "
        f"You might enjoy {', '.join(titles)}. Would you like to read a summary of any of these?"
    )
    return response
```

**Current implementation:** The chatbot uses a **template-based response generation** rather than calling an external LLM (like OpenAI GPT). This design choice means:
- **No API costs** — the chatbot runs entirely locally.
- **No external dependency** — works without internet access to AI APIs.
- **Deterministic responses** — the output is predictable and safe.
- **RAG-ready** — the architecture is designed so that an LLM can be plugged in later. The `context_books` retrieved by semantic search would serve as the context window for an LLM prompt.

The chatbot is exposed via `POST /ai/chat` and requires authentication:

```python
@router.post("/chat", response_model=ChatResponse)
def ask_chatbot(request: ChatRequest, db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)):
    reply = process_chat(request.query, current_user.id, db)
    return ChatResponse(reply=reply)
```

### 2.5 Embedding Generation & Storage

**Location:** `backend/src/services/ai_service.py:24-40`

Each book in the system has a corresponding **384-dimensional vector** stored in the `book_embeddings` table. The embedding is generated from a concatenation of the book's key text fields:

```python
def generate_book_embedding(book: models.Book, db: Session):
    text_to_embed = f"{book.title} {book.author} {book.genre} {book.description or ''}"
    vector = get_embedding(text_to_embed)
    # ...store or update in database
```

The text that gets embedded includes:
- **Title** — The book's name.
- **Author** — The author(s).
- **Genre** — The book's genre classification.
- **Description** — The book's full description.

This composite text ensures the embedding captures thematic, topical, and stylistic information about the book.

Embeddings are stored using the **pgvector** SQLAlchemy type:

```python
class BookEmbedding(Base):
    __tablename__ = "book_embeddings"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, unique=True)
    embedding = Column(Vector(384))  # 384 dimensions for all-MiniLM-L6-v2
    model_version = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

### 2.6 AI Service Architecture

The AI service is organized as a single Python module (`backend/src/services/ai_service.py`) containing all AI logic. This keeps the AI layer clean and separated from the HTTP routing layer.

**Data flow:**

```
User Query (text)
    │
    ▼
get_embedding(query)          ← Sentence-BERT encodes text to 384-dim vector
    │
    ▼
pgvector cosine_distance()    ← PostgreSQL compares against stored book vectors
    │
    ▼
Sorted Results (nearest books)
    │
    ▼
Response to User
```

---

## 3. How the Admin Dashboard Works

**Location:** `frontend/src/pages/AdminDashboard.tsx`, `backend/src/routers/admin.py`

The admin dashboard is a comprehensive management interface accessible only to users with the `admin` role. It provides tools for managing books, orders, users, and viewing analytics.

### 3.1 Authentication & Access Control

**Backend:** `backend/src/utils/dependencies.py:40-45`

Admin access is enforced at the API level using **role-based access control (RBAC)**:

```python
def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return current_user
```

All admin endpoints depend on `get_current_admin_user`, which:
1. Extracts the JWT token from the request header.
2. Decodes and validates the token.
3. Loads the user from the database.
4. Checks that the user's `role` field equals `"admin"`.
5. Returns HTTP 403 Forbidden if the check fails.

**Frontend:** The dashboard component checks the user's role on render and redirects non-admin users:

```tsx
if (user?.role !== 'admin') {
    return <Navigate to="/" />;
}
```

**Admin creation:** The first user to register in the system automatically becomes an admin (`backend/src/routers/auth.py:39-40`):

```python
count = db.query(models.User).count()
role = models.UserRole.admin if count == 0 else models.UserRole.user
```

### 3.2 Analytics Overview

**Endpoint:** `GET /admin/analytics`

The dashboard displays seven analytics cards at the top of the page:

| Metric | Description |
|--------|-------------|
| **Total Books** | Count of all books in the catalog |
| **Total Users** | Count of all registered users |
| **Total Orders** | Count of all orders placed |
| **Total Revenue** | Sum of all order `total_price` values |
| **New Users (7d)** | Users who registered in the last 7 days |
| **Admins** | Count of users with the admin role |
| **Completed Orders** | Count of orders with status "completed" |

The analytics endpoint (`backend/src/routers/admin.py:95-143`) aggregates data using SQLAlchemy queries:

```python
@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db), ...):
    total_users = db.query(models.User).count()
    total_books = db.query(models.Book).count()
    total_orders = db.query(models.Order).count()
    revenue = db.query(func.sum(models.Order.total_price)).scalar()
    # ... orders by status, users by role, recent signups
```

### 3.3 Book Management (CRUD)

The admin can perform full CRUD operations on books:

**Adding a book** (`POST /books/`):
- The admin fills out a form with: title, author, price, genre, description, ISBN, publisher, publication date, cover image URL, and stock count.
- The genre field supports both a dropdown of predefined genres and a custom text input.
- On submission, the book record is created in the database.
- **Automatically**, an embedding vector is generated for the new book and stored.

**Editing a book** (`PUT /books/{id}`):
- Clicking the pencil icon on any book row populates the form with the book's current data.
- The admin modifies fields and submits.
- The book record is updated in the database.

**Deleting a book** (`DELETE /books/{id}`):
- Clicking the trash icon triggers a confirmation dialog.
- On confirmation, the book and its associated embedding are deleted.

**Genre filtering:** The catalog table includes a genre dropdown that filters the displayed books client-side.

### 3.4 Order Management

**Endpoint:** `GET /orders/all` (admin only)

The Orders tab displays a table of all orders with:
- Order ID
- Customer username
- Line items (book titles and quantities)
- Total price
- Current status (pending/completed/cancelled) with color-coded badges
- Order date
- A dropdown to **update order status**

Status updates are sent via `PATCH /orders/{id}/status`.

### 3.5 User Management

**Endpoints:** `GET /admin/users`, `PATCH /admin/users/{id}`, `DELETE /admin/users/{id}`

The Users tab displays a table of all registered users with:
- User ID, username, email
- Role (with a dropdown to change between "user" and "admin")
- Active/Inactive status badge
- Registration date
- Action buttons to activate/deactivate or delete users

**Safety constraints:**
- Admins cannot modify their own account from the admin panel (prevents self-demotion/deletion).
- Deactivating a user prevents them from logging in.
- Deleting a user removes their record from the database.

### 3.6 Search Vector Reindexing

**Endpoint:** `POST /ai/reindex`

The dashboard includes a "Reindex Search Vectors" button that:
1. Fetches all books from the database.
2. Regenerates the embedding vector for each book.
3. Updates (or creates) the corresponding `BookEmbedding` record.

This is useful when:
- The embedding model is updated.
- Book descriptions have been changed.
- Embeddings have been corrupted or lost.

```python
@router.post("/reindex", response_model=dict)
def reindex_all_books(db: Session = Depends(get_db), ...):
    books = db.query(models.Book).all()
    count = 0
    for book in books:
        generate_book_embedding(book, db)
        count += 1
    return {"message": f"Successfully re-indexed {count} books"}
```

### 3.7 Frontend Implementation Details

The admin dashboard is a single React component (`AdminDashboard.tsx`) that:

- Uses **tab navigation** (Books, Orders, Users) with URL state management.
- Fetches all data in parallel on mount using `Promise.all()`.
- Renders analytics cards in a responsive grid (2 columns on mobile, 4 on tablet, 7 on desktop).
- Uses **Lucide React** icons throughout.
- Implements inline editing with a collapsible form panel.
- Supports genre filtering via a dropdown that reads from the `/books/genres` endpoint.
- Uses Tailwind CSS for all styling with a consistent indigo/slate color scheme.

---

## 4. How Semantic Search Works

### 4.1 What is Semantic Search?

Traditional keyword search matches exact words. If you search "thriller," it only finds books containing the word "thriller" in their title, author, or description.

**Semantic search** understands **meaning**. It converts both the search query and the book metadata into mathematical representations (vectors) in a high-dimensional space. Books that are "close" to the query in this space are returned as results, even if they don't share any exact words with the query.

For example, searching "scary murder mystery" would match books tagged as "Thriller" or "Crime" because the embedding model understands that these concepts are semantically related.

### 4.2 The Embedding Pipeline

**Step 1: Book Ingestion**

When a book is added to the system, its metadata is concatenated into a single text string:

```
"{title} {author} {genre} {description}"
```

For example:
```
"Things Fall Apart Chinua Achebe Fiction A classic of modern African literature, depicting pre-colonial life in Nigeria and the arrival of Europeans."
```

This text is passed to the Sentence-BERT model, which produces a 384-dimensional floating-point vector. This vector is stored in the `book_embeddings` table.

**Step 2: Query Processing**

When a user enters a search query, the same model encodes the query text into a 384-dimensional vector using the exact same encoding process.

**Step 3: Similarity Search**

The system uses pgvector's cosine distance operator (`<=>`) to compare the query vector against all stored book vectors directly in PostgreSQL:

```sql
SELECT * FROM book_embeddings
ORDER BY embedding <=> $query_vector
LIMIT 5;
```

This is executed as a full table scan with distance computation. For the prototype scale (hundreds to low thousands of books), this is performant enough. For production scale, an IVFFlat or HNSW index would be added.

### 4.3 Vector Similarity with pgvector

**Database:** PostgreSQL with the `pgvector` extension.

The `ankane/pgvector:latest` Docker image is used, which bundles PostgreSQL with pgvector pre-installed. The SQLAlchemy model uses pgvector's `Vector` column type:

```python
from pgvector.sqlalchemy import Vector

embedding = Column(Vector(384))
```

The cosine distance is computed using pgvector's built-in operator:

```python
.order_by(models.BookEmbedding.embedding.cosine_distance(query_vector))
```

This translates to the SQL `<=>` operator, which computes `1 - cosine_similarity`. A distance of 0 means identical vectors; a distance of 2 means opposite vectors.

### 4.4 Query Processing Flow

```
┌─────────────────┐
│  User types:    │
│  "beginner      │
│   books on ML"  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Sentence-BERT   │
│ encodes query   │
│ → 384-dim vector│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ PostgreSQL + pgvector               │
│                                     │
│ SELECT book_id,                     │
│   embedding <=> $query_vector       │
│   AS distance                       │
│ FROM book_embeddings                │
│ ORDER BY distance ASC               │
│ LIMIT 5;                            │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Top 5 books     │
│ returned to     │
│ user            │
└─────────────────┘
```

### 4.5 Cosine Distance Explained

Cosine distance measures the **angle** between two vectors, not their magnitude. This is important because:
- Two books might have different "weights" in their embeddings (e.g., a long description vs. a short one), but if they're about the same topic, the angle between their vectors will be small.
- Cosine distance ranges from 0 (identical direction) to 2 (opposite direction).
- For text embeddings, distances typically fall between 0.2 and 1.5 for semantically related content.

### 4.6 Fallback Mechanism

If semantic search is unavailable (e.g., the embedding model fails to load), the system falls back to **keyword search** using SQL `ILIKE` pattern matching:

```python
# In the books router - regular keyword search
if search:
    search_filter = f"%{search}%"
    query = query.filter(
        or_(
            models.Book.title.ilike(search_filter),
            models.Book.author.ilike(search_filter),
            models.Book.description.ilike(search_filter),
        )
    )
```

The frontend allows users to toggle between "AI Semantic" and "Keyword" search modes.

### 4.7 Frontend Search Modes

**Location:** `frontend/src/pages/Home.tsx:63-95`

The homepage search bar supports two modes:

1. **AI Semantic** (default): Calls `GET /ai/search` which uses the vector similarity search described above.
2. **Keyword**: Tries the genre-based recommendation search first (`GET /books/search-with-recommendations`), and falls back to regular ILIKE search if no exact title match is found.

The user can switch between modes using radio buttons below the search bar.

---

## 5. How Books Get Into the System

There are three methods for adding books to the system, each suited for different scenarios.

### 5.1 Admin Manual Entry

**Endpoint:** `POST /books/`
**Frontend:** Admin Dashboard → Books Tab → "Add New Book" form

An admin can manually add a single book through the dashboard form. The form accepts:

| Field | Required | Description |
|-------|----------|-------------|
| Title | Yes | Book title |
| Author | Yes | Author name(s) |
| Price | Yes | Decimal price (e.g., 12.99) |
| Genre | Yes | Selected from dropdown or custom text |
| Description | No | Full book description |
| ISBN | No | International Standard Book Number |
| Publisher | No | Publishing house name |
| Publication Date | No | Date picker |
| Cover Image URL | No | URL to the book's cover image |
| Stock Count | No | Number of copies available |

When submitted, the backend:
1. Creates a `Book` record in the database.
2. Automatically generates and stores the embedding vector.

```python
@router.post("/", response_model=schemas.BookRead, status_code=status.HTTP_201_CREATED)
def create_book(book_in: schemas.BookCreate, db: Session = Depends(get_db), ...):
    book = models.Book(**book_in.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    generate_book_embedding(book, db)  # Auto-generate embedding
    return book
```

### 5.2 Seed Script (Small Dataset)

**Location:** `backend/seed_books.py`

This script seeds **25 curated books** into the database. It is designed for initial setup and testing. The books include well-known titles across multiple genres:

- **Fiction:** Things Fall Apart, 1984, To Kill a Mockingbird, The Alchemist, Pride and Prejudice, etc.
- **Technology:** Clean Code, Introduction to Algorithms, Python Crash Course, Deep Learning
- **Business:** The Lean Startup, Rich Dad Poor Dad, Zero to One
- **History:** Sapiens, Guns Germs and Steel
- **Science:** A Brief History of Time, The Selfish Gene
- **Biography:** Becoming, Educated
- **Psychology:** Thinking Fast and Slow
- **Self-Help:** Atomic Habits
- **Philosophy:** The Art of War, Meditations
- **Fantasy:** The Hobbit

**How to run:**
```bash
cd backend
python seed_books.py
```

The script:
1. Checks if books already exist (skips if they do to avoid duplicates).
2. Creates each book record.
3. Generates and stores an embedding for each book.
4. Uses cover images from the Open Library Covers API.

### 5.3 Bulk Seed Script (1000+ Books)

**Location:** `backend/seed_books_bulk.py`

This is the primary method for populating the system with a large catalog. It fetches **real books from the Open Library API** and generates embeddings in batches.

**How to run:**
```bash
cd backend
python seed_books_bulk.py           # Seeds 1000 books (default)
python seed_books_bulk.py 500       # Seeds 500 books
python seed_books_bulk.py reseed    # Clears and re-seeds 1000 books
python seed_books_bulk.py clear     # Removes all books
python seed_books_bulk.py fix-covers # Fixes broken cover image URLs
```

**Process:**

1. **Fetch from Open Library:** The script queries the Open Library Search API (`https://openlibrary.org/search.json`) with 84 different search queries covering diverse genres (fiction, science, technology, philosophy, cooking, etc.). Each query fetches up to 200 results (2 pages of 100).

2. **Deduplicate:** Books are deduplicated by title + author combination to avoid repeats across different search queries.

3. **Convert to internal format:** Each Open Library result is converted to the internal book schema:
   - Title, author, publisher are extracted.
   - Genre is mapped from Open Library subject tags using keyword matching (`map_subject_to_genre()`).
   - Price is randomly generated between $5.99 and $49.99.
   - Stock count is randomly generated between 5 and 200.
   - Rating is randomly generated between 3.0 and 5.0.
   - Cover images are built from Open Library's cover ID system.

4. **Batch insert:** Books are inserted in batches of 100 using `db.bulk_save_objects()` for performance.

5. **Batch embedding generation:** After all books are inserted, embeddings are generated in batches. The Sentence-BERT model's `encode()` method supports batch processing, so it encodes 100 texts at a time:

   ```python
   texts = [f"{b.title} {b.genre} {b.description or ''}" for b in batch_books]
   vectors = model.encode(texts).tolist()  # Batch encode
   ```

6. **Create database indexes:** After seeding, indexes are created on genre, author, title, and price columns for query performance.

**Genre mapping:** The `map_subject_to_genre()` function maps Open Library's free-form subject tags to the system's predefined genre list using keyword matching. For example:
- Subjects containing "science fiction", "sci-fi", "space", "dystopia" → "Science Fiction"
- Subjects containing "fantasy", "magic", "dragon" → "Fantasy"
- Subjects containing "computer", "programming", "software" → "Technology"
- If no match is found, defaults to "Fiction"

### 5.4 Book Data Model

**Location:** `backend/src/models.py:59-84`

```python
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    genre = Column(String, index=True, nullable=False)
    description = Column(Text)
    isbn = Column(String, unique=True, index=True)
    publisher = Column(String)
    publication_date = Column(DateTime)
    price = Column(DECIMAL(10, 2), nullable=False)
    cover_image_url = Column(String)
    stock_count = Column(Integer, default=0)
    average_rating = Column(DECIMAL(3, 2), default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=..., onupdate=...)

    # Relationships
    embeddings = relationship("BookEmbedding", back_populates="book")
    order_items = relationship("OrderItem", back_populates="book")
    cart_items = relationship("CartItem", back_populates="book")
    browsing_history = relationship("UserBrowsingHistory", back_populates="book")
```

Key design decisions:
- **Price uses `DECIMAL(10,2)`** — avoids floating-point precision issues with financial data.
- **Average rating uses `DECIMAL(3,2)`** — supports ratings like 4.75.
- **ISBN is unique** — prevents duplicate book entries.
- **Genre is a string, not an enum** — allows flexible genre values (including custom genres from the admin form).
- **Timestamps are auto-managed** — `created_at` and `updated_at` use UTC timestamps.

### 5.5 Automatic Embedding on Ingestion

Every time a book is created via the admin API (`POST /books/`), the system automatically generates and stores its embedding vector. This ensures that:

- New books are **immediately searchable** via semantic search.
- New books are **immediately available** for recommendations.
- No manual step is required after adding a book.

When a book is updated (`PUT /books/{id}`), the embedding is **not** automatically regenerated. The admin must trigger a reindex from the dashboard if they want updated embeddings for modified books.

---

## 6. Tech Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript | UI framework |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **State** | React Context API | Auth & cart state |
| **HTTP Client** | Axios | API communication |
| **Routing** | React Router v6 | Client-side navigation |
| **Icons** | Lucide React | UI icons |
| **Backend** | Python 3.11 + FastAPI | API framework |
| **ORM** | SQLAlchemy | Database access |
| **Migrations** | Alembic | Schema versioning |
| **Auth** | JWT (python-jose) + bcrypt | Token-based auth |
| **Database** | PostgreSQL 15+ | Primary data store |
| **Vector Store** | pgvector | Embedding storage & search |
| **AI Model** | Sentence-BERT (all-MiniLM-L6-v2) | Text embeddings |
| **Container** | Docker Compose | Local development |

---

## 7. Database Schema

```
┌──────────────────────┐       ┌──────────────────────┐
│        users         │       │        books          │
├──────────────────────┤       ├──────────────────────┤
│ id (PK)              │       │ id (PK)              │
│ username (UNIQUE)    │       │ title                │
│ email (UNIQUE)       │       │ author               │
│ hashed_password      │       │ genre                │
│ role (user|admin)    │       │ description          │
│ is_active            │       │ isbn (UNIQUE)        │
│ created_at           │       │ publisher            │
│ updated_at           │       │ publication_date     │
└──────────┬───────────┘       │ price (DECIMAL)      │
           │                   │ cover_image_url      │
           │                   │ stock_count          │
           │                   │ average_rating       │
           │                   │ created_at           │
           │                   │ updated_at           │
           │                   └──────────┬───────────┘
           │                              │
           │    ┌─────────────────────────┐│
           │    │    book_embeddings      ││
           │    ├─────────────────────────┤│
           │    │ id (PK)                 ││
           │    │ book_id (FK → books)    │◄┘
           │    │ embedding (Vector(384)) │
           │    │ model_version           │
           │    │ created_at              │
           │    └─────────────────────────┘
           │
           │    ┌─────────────────────────┐
           │    │     cart_items          │
           │    ├─────────────────────────┤
           ├───►│ id (PK)                 │
           │    │ user_id (FK → users)    │
           │    │ book_id (FK → books)    │
           │    │ quantity                │
           │    │ added_at                │
           │    └─────────────────────────┘
           │
           │    ┌─────────────────────────┐       ┌─────────────────────┐
           │    │        orders           │       │    order_items      │
           │    ├─────────────────────────┤       ├─────────────────────┤
           ├───►│ id (PK)                 │◄──────│ id (PK)             │
           │    │ user_id (FK → users)    │       │ order_id (FK)       │
           │    │ total_price (DECIMAL)   │       │ book_id (FK)        │
           │    │ status (pending|        │       │ quantity            │
           │    │   completed|cancelled)  │       │ unit_price          │
           │    │ created_at              │       └─────────────────────┘
           │    │ updated_at              │
           │    └─────────────────────────┘
           │
           │    ┌─────────────────────────┐
           │    │  user_browsing_history  │
           │    ├─────────────────────────┤
           └───►│ id (PK)                 │
                │ user_id (FK → users)    │
                │ book_id (FK → books)    │
                │ event_type (view|       │
                │   cart_add|purchase)    │
                │ timestamp               │
                └─────────────────────────┘
```

---

## 8. API Architecture

The backend exposes a RESTful API organized into routers:

| Router | Prefix | Endpoints | Auth Required |
|--------|--------|-----------|---------------|
| **Auth** | `/auth` | `POST /register`, `POST /login`, `GET /me` | Login/Register: No; Me: Yes |
| **Books** | `/books` | `GET /`, `GET /{id}`, `POST /`, `PUT /{id}`, `DELETE /{id}`, `GET /genres`, `GET /search-with-recommendations` | Read: No; Write: Admin |
| **AI** | `/ai` | `GET /search`, `GET /recommendations`, `POST /chat`, `POST /reindex` | Search: No; Others: Yes; Reindex: Admin |
| **Cart** | `/cart` | `GET /`, `POST /`, `PUT /{id}`, `DELETE /{id}` | Yes |
| **Orders** | `/orders` | `GET /`, `POST /checkout`, `GET /all`, `PATCH /{id}/status` | Yes; All/Status: Admin |
| **Users** | `/users` | `GET /reading-history` | Yes |
| **Admin** | `/admin` | `GET /users`, `PATCH /users/{id}`, `DELETE /users/{id}`, `GET /analytics` | Admin |

---

## 9. Frontend Architecture

The frontend is a React SPA with the following page structure:

| Page | Route | Description |
|------|-------|-------------|
| **Home** | `/` | Catalog with search, recommendations, genre filtering |
| **Book Detail** | `/book/:id` | Full book info with add-to-cart |
| **Cart** | `/cart` | Shopping cart with quantity management |
| **Orders** | `/orders` | User's order history |
| **Login** | `/login` | Login form |
| **Register** | `/register` | Registration form |
| **Admin Dashboard** | `/admin` | Full admin management (books, orders, users, analytics) |

**Shared components:**
- `Layout.tsx` — Navigation bar and page wrapper.
- `Chatbot.tsx` — Floating AI chat widget (available on all pages).
- `ReadingHistory.tsx` — Displays user's recently viewed books.

**Context providers:**
- `AuthContext` — Manages user authentication state, JWT token, login/logout.
- `CartContext` — Manages shopping cart state.

---

## 10. Security Implementation

| Concern | Implementation |
|---------|---------------|
| **Password Hashing** | bcrypt with SHA-256 pre-hashing (`bcrypt_sha256` scheme) |
| **Authentication** | JWT tokens with 30-minute expiry |
| **Token Storage** | localStorage on the client |
| **Token Transmission** | `Authorization: Bearer <token>` header |
| **RBAC** | `get_current_admin_user` dependency checks role |
| **CORS** | Configured to allow all origins (development setting) |
| **SQL Injection** | Prevented by SQLAlchemy's parameterized queries |
| **Input Validation** | Pydantic schemas validate all request bodies |
| **Environment Variables** | Database URL and secret key loaded from `.env` |

---

## 11. Deployment & Infrastructure

**Docker Compose** (`compose.yml`) provides two services:

1. **db** — PostgreSQL with pgvector extension (`ankane/pgvector:latest`), exposed on port 5433.
2. **pgadmin** — pgAdmin4 web interface for database management, exposed on port 5050.

**Environment configuration:**
- Database URL: `postgresql://postgres:password@localhost:5433/bookshop`
- Secret key: Loaded from `SECRET_KEY` environment variable (defaults to a development value).

**Running the system:**
```bash
# Start database
docker compose up -d

# Start backend
cd backend
uvicorn src.main:app --reload

# Seed books
python seed_books_bulk.py

# Start frontend
cd frontend
pnpm install
pnpm run dev
```

---

*End of Report*
